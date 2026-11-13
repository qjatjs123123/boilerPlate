"""스키마 테스트 — DB 설계(data-model.yaml)와 실제 모델(Base.metadata)을 기계 검증한다.

1. 설계 일치: data-model.yaml 과 모델이 테이블·컬럼·제약까지 1:1 로 같아야 한다.
2. 정규화·규약: 목록을 문자열/JSON 으로 저장, 반복 컬럼, 다른 테이블 값 복사 등을 차단한다.
3. 테이블 간: 모양이 거의 같은 테이블(중복 의심)을 찾는다.
   앱 코드 어디에서도 쓰지 않는 테이블(unused_table_report)은 주간 점검(scripts/gc)이 보고만 한다 —
   spec-run 은 models Task 다음에 repository Task 를 하므로, 개발 중엔 잠깐 미사용이 정상이다.
4. 등록: 도메인 models 가 alembic/env.py 에 import 되어 있어야 한다.
위반 메시지는 그대로 에이전트 컨텍스트가 된다. 기존 위반은 known-violations.json 래칫(줄이기만 가능).
"""

import ast
import importlib
import inspect
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from sqlalchemy import (
    ARRAY,
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    Numeric,
    PickleType,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
)

from app.db.base import Base
from tests.architecture._violations import (
    BACKEND_ROOT,
    RULES,
    STALE_MESSAGE,
    Violation,
    new_violation_messages,
    stale_known_keys,
)

DOMAINS_DIR = BACKEND_ROOT / "app" / "domains"
DATA_MODEL_PATH = BACKEND_ROOT / "data-model.yaml"
ALEMBIC_ENV_PATH = BACKEND_ROOT / "alembic" / "env.py"
DATA_MODEL_FILE = "data-model.yaml"
DESIGN_DOC = f"{RULES}/db-design.md"
MODEL_DOC = f"{RULES}/model-layer.md"

# isinstance 검사 순서가 중요하다 — 하위 타입(Enum ⊂ String, Text ⊂ String, Float ⊂ Numeric)을 먼저
TYPE_NAMES: list[tuple[type, str]] = [
    (Enum, "enum"),
    (Boolean, "boolean"),
    (BigInteger, "biginteger"),
    (SmallInteger, "integer"),
    (Integer, "integer"),
    (Text, "text"),
    (String, "string"),
    (DateTime, "datetime"),
    (Date, "date"),
    (Float, "float"),
    (Numeric, "decimal"),
]
FORBIDDEN_TYPES = (JSON, ARRAY, PickleType)
COLUMN_KEYS = {
    "type",
    "length",
    "values",
    "primary_key",
    "nullable",
    "unique",
    "index",
    "foreign_key",
    "ondelete",
    "denormalized",
}
TABLE_KEYS = {"description", "association", "columns", "unique_constraints", "distinct_from"}
TIMESTAMP_COLUMNS = ("created_at", "updated_at")
LIST_SUFFIXES = ("_ids", "_list", "_csv", "_array")
DERIVED_SUFFIXES = ("_count", "_total", "_sum")
COPIED_ATTRIBUTES = {"name", "username", "nickname", "email", "title", "phone"}
IRREGULAR_PLURALS = {"data", "media", "people", "children", "series", "news", "staff", "feedback", "information"}
REPEATING_COLUMN_PATTERN = re.compile(r"^(?P<prefix>.+?)_?\d+$")
APP_DIR = BACKEND_ROOT / "app"
# 두 테이블의 FK 대상이 같고, id·타임스탬프를 뺀 (컬럼명, 타입) 겹침이 이 비율 이상이면 중복 의심
SIMILAR_TABLE_RATIO = 0.8


def _is_schema_rule(rule: str) -> bool:
    """이 테스트가 소유한 규칙"""
    return rule.startswith("schema-")


# ---------- 모델 로드 ----------


@dataclass
class TableSource:
    """테이블이 정의된 위치"""

    file: str
    line: int
    class_name: str = ""


def _domain_model_modules() -> list[str]:
    """models.py 가 있는 도메인 이름 목록"""
    return sorted(
        path.name
        for path in DOMAINS_DIR.iterdir()
        if path.is_dir() and not path.name.startswith("_") and (path / "models.py").exists()
    )


def _load_table_sources() -> dict[str, TableSource]:
    """모든 도메인 models 를 import 하고 테이블명 → 정의 위치"""
    sources: dict[str, TableSource] = {}
    for domain in _domain_model_modules():
        module = importlib.import_module(f"app.domains.{domain}.models")
        file = f"app/domains/{domain}/models.py"
        for value in vars(module).values():
            if isinstance(value, Table):
                sources[value.name] = TableSource(file, 0)
            elif inspect.isclass(value) and value.__module__ == module.__name__ and hasattr(value, "__table__"):
                sources[value.__table__.name] = TableSource(file, inspect.getsourcelines(value)[1], value.__name__)
    return sources


# ---------- 설계(data-model.yaml) 로드 ----------


@dataclass
class DesignedTable:
    """data-model.yaml 의 테이블 1개"""

    name: str
    description: str
    is_association: bool
    columns: dict[str, dict[str, object]]
    unique_constraints: dict[str, list[str]] = field(default_factory=dict)
    distinct_from: dict[str, str] = field(default_factory=dict)


def _load_design() -> dict[str, DesignedTable]:
    """data-model.yaml → 테이블명 → DesignedTable"""
    document = yaml.safe_load(DATA_MODEL_PATH.read_text(encoding="utf-8")) or {}
    tables = document.get("tables") or {}
    return {
        name: DesignedTable(
            name=name,
            description=(spec or {}).get("description", ""),
            is_association=bool((spec or {}).get("association", False)),
            columns=(spec or {}).get("columns") or {},
            unique_constraints=(spec or {}).get("unique_constraints") or {},
            distinct_from=(spec or {}).get("distinct_from") or {},
        )
        for name, spec in tables.items()
    }


def _design_violation(detail: str, rule: str = "schema-data-model-invalid") -> Violation:
    """data-model.yaml 자체의 위반"""
    return Violation(DATA_MODEL_FILE, 0, rule, detail, DESIGN_DOC)


def _validate_design_table(table: DesignedTable) -> list[Violation]:
    """설계 문서 형식 검사 — 오타 키, 필수값 누락"""
    found: list[Violation] = []
    if not table.description:
        found.append(_design_violation(f"{table.name}: description(이 테이블이 저장하는 것) 누락"))
    for column_name, spec in table.columns.items():
        unknown_keys = set(spec) - COLUMN_KEYS
        if unknown_keys:
            found.append(_design_violation(f"{table.name}.{column_name}: 알 수 없는 속성 {sorted(unknown_keys)}"))
        if "denormalized" in spec and not str(spec["denormalized"]).strip():
            found.append(_design_violation(f"{table.name}.{column_name}: denormalized 사유가 비어 있음"))
    for other_name, reason in table.distinct_from.items():
        if not str(reason or "").strip():
            found.append(_design_violation(f"{table.name}.distinct_from.{other_name}: 따로 두는 사유가 비어 있음"))
    return found


def _validate_design(raw_tables: dict[str, object], design: dict[str, DesignedTable]) -> list[Violation]:
    """설계 문서 전체 형식 검사"""
    found: list[Violation] = []
    for name, spec in raw_tables.items():
        unknown_keys = set(spec or {}) - TABLE_KEYS
        if unknown_keys:
            found.append(_design_violation(f"{name}: 알 수 없는 테이블 속성 {sorted(unknown_keys)}"))
    for table in design.values():
        found += _validate_design_table(table)
    return found


# ---------- 실제 모델 → 설계 형식으로 변환 ----------


def _type_name(column: Column) -> str:
    """SQLAlchemy 타입 → data-model.yaml 타입명"""
    for type_class, name in TYPE_NAMES:
        if isinstance(column.type, type_class):
            return name
    return type(column.type).__name__.lower()


def _describe_foreign_key(column: Column) -> dict[str, object]:
    """FK 정보 (없으면 빈 dict)"""
    foreign_keys = list(column.foreign_keys)
    if not foreign_keys:
        return {}
    foreign_key = foreign_keys[0]
    return {"foreign_key": foreign_key.target_fullname, "ondelete": foreign_key.ondelete}


def _describe_column(column: Column) -> dict[str, object]:
    """실제 컬럼을 설계 문서와 같은 형식의 dict 로"""
    described: dict[str, object] = {
        "type": _type_name(column),
        "primary_key": bool(column.primary_key),
        "nullable": bool(column.nullable),
        "unique": bool(column.unique),
        "index": bool(column.index),
    }
    if isinstance(column.type, Enum):
        described["values"] = list(column.type.enums)
    elif isinstance(column.type, String) and column.type.length is not None:
        described["length"] = column.type.length
    return described | _describe_foreign_key(column)


def _normalize_designed_column(spec: dict[str, object]) -> dict[str, object]:
    """설계 컬럼에 기본값을 채워 비교 가능한 형태로"""
    is_primary_key = bool(spec.get("primary_key", False))
    normalized = {
        "type": spec.get("type"),
        "primary_key": is_primary_key,
        "nullable": bool(spec.get("nullable", not is_primary_key)),
        "unique": bool(spec.get("unique", False)),
        "index": bool(spec.get("index", False)),
    }
    for optional_key in ("length", "values", "foreign_key", "ondelete"):
        if optional_key in spec:
            normalized[optional_key] = spec[optional_key]
    return normalized


def _named_unique_constraints(table: Table) -> dict[str, list[str]]:
    """테이블 수준 UniqueConstraint (이름 → 컬럼)"""
    return {
        str(constraint.name): [column.name for column in constraint.columns]
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint) and constraint.name
    }


# ---------- 1. 설계 일치 ----------


def _column_differences(table_name: str, designed: DesignedTable, table: Table) -> list[str]:
    """컬럼 단위 차이 설명 목록"""
    differences: list[str] = []
    for column_name in sorted(set(designed.columns) - set(table.c.keys())):
        differences.append(f"{table_name}.{column_name}: 설계에는 있는데 모델에 없음")
    for column_name in sorted(set(table.c.keys()) - set(designed.columns)):
        differences.append(f"{table_name}.{column_name}: 모델에는 있는데 설계에 없음")
    for column_name in sorted(set(designed.columns) & set(table.c.keys())):
        expected = _normalize_designed_column(designed.columns[column_name])
        actual = _describe_column(table.c[column_name])
        for key in sorted(set(expected) | set(actual)):
            if expected.get(key) != actual.get(key):
                differences.append(
                    f"{table_name}.{column_name}.{key}: 설계={expected.get(key)!r}, 모델={actual.get(key)!r}"
                )
    return differences


def _table_differences(designed: DesignedTable, table: Table) -> list[str]:
    """테이블 1개의 설계-모델 차이"""
    differences = _column_differences(designed.name, designed, table)
    actual_constraints = _named_unique_constraints(table)
    if designed.unique_constraints != actual_constraints:
        differences.append(
            f"{designed.name}.unique_constraints: 설계={designed.unique_constraints!r}, 모델={actual_constraints!r}"
        )
    return differences


def _check_design_match(design: dict[str, DesignedTable], sources: dict[str, TableSource]) -> list[Violation]:
    """data-model.yaml ↔ Base.metadata 1:1 비교"""
    found: list[Violation] = []
    tables = Base.metadata.tables
    for name in sorted(set(tables) - set(design)):
        source = sources.get(name, TableSource("app/domains", 0))
        detail = f"{name}: 설계 없이 만든 테이블 — data-model.yaml 에 먼저 설계"
        found.append(Violation(source.file, source.line, "schema-undesigned-table", detail, DESIGN_DOC))
    for name in sorted(set(design) - set(tables)):
        found.append(_design_violation(f"{name}: 설계에는 있는데 모델이 없음", "schema-spec-mismatch"))
    for name in sorted(set(design) & set(tables)):
        source = sources.get(name, TableSource("app/domains", 0))
        for detail in _table_differences(design[name], tables[name]):
            found.append(Violation(source.file, source.line, "schema-spec-mismatch", detail, DESIGN_DOC))
    return found


# ---------- 2. 정규화·규약 ----------


@dataclass
class TableContext:
    """정규화 검사에 필요한 테이블 정보"""

    table: Table
    source: TableSource
    design: DesignedTable | None

    @property
    def is_association(self) -> bool:
        """N:M 연결 테이블 여부"""
        return self.design is not None and self.design.is_association

    def violation(self, rule: str, detail: str, doc: str = DESIGN_DOC) -> Violation:
        """이 테이블 위치로 위반 생성"""
        return Violation(self.source.file, self.source.line, rule, f"{self.table.name}: {detail}", doc)


def _check_repeating_columns(context: TableContext) -> list[Violation]:
    """phone_1, phone_2 같은 반복 컬럼"""
    groups: dict[str, list[str]] = {}
    for column_name in context.table.c.keys():
        match = REPEATING_COLUMN_PATTERN.match(column_name)
        if match:
            groups.setdefault(match.group("prefix"), []).append(column_name)
    return [
        context.violation("schema-repeating-columns", f"반복 컬럼 {sorted(names)} → 자식 테이블로 분리")
        for names in groups.values()
        if len(names) >= 2
    ]


def _check_list_columns(context: TableContext) -> list[Violation]:
    """여러 값을 컬럼 하나에 몰아 넣은 경우 (콤마 문자열·JSON·다른 테이블 이름의 컬럼)"""
    found: list[Violation] = []
    table_names = set(Base.metadata.tables)
    for column in context.table.c:
        if isinstance(column.type, FORBIDDEN_TYPES):
            detail = f"{column.name} 이 {_type_name(column)} 타입 — 구조화된 값은 별도 테이블로"
            found.append(context.violation("schema-json-column", detail))
        elif column.name.endswith(LIST_SUFFIXES) or column.name in table_names:
            detail = f"{column.name} 은 여러 값을 한 컬럼에 저장 — 자식 테이블 또는 연결 테이블로"
            found.append(context.violation("schema-list-in-column", detail))
    return found


def _copied_column_candidates(context: TableContext) -> dict[str, set[str]]:
    """FK 접두사(author_id → author) → 대상 테이블 컬럼명 + 흔한 복사 속성"""
    candidates: dict[str, set[str]] = {}
    for column in context.table.c:
        for foreign_key in column.foreign_keys:
            prefix = column.name.removesuffix("_id")
            target_columns = set(foreign_key.column.table.c.keys()) - {"id", *TIMESTAMP_COLUMNS}
            candidates[prefix] = target_columns | COPIED_ATTRIBUTES
    return candidates


def _check_copied_columns(context: TableContext) -> list[Violation]:
    """FK 로 연결된 테이블의 값을 복사해 둔 컬럼 (author_id 가 있는데 author_name)"""
    found: list[Violation] = []
    for prefix, attributes in _copied_column_candidates(context).items():
        for attribute in sorted(attributes):
            column_name = f"{prefix}_{attribute}"
            if column_name in context.table.c:
                detail = f"{column_name} 은 {prefix}_id 로 연결된 값의 복사본 — 저장하지 말고 relationship 으로 조회"
                found.append(context.violation("schema-copied-column", detail))
    return found


def _check_derived_columns(context: TableContext) -> list[Violation]:
    """개수·합계 컬럼은 설계에 비정규화 사유가 있어야 한다"""
    designed_columns = context.design.columns if context.design else {}
    return [
        context.violation(
            "schema-denormalized-unmarked",
            f"{column_name} 은 계산 가능한 값 — 저장하려면 data-model.yaml 에 denormalized 사유 필요",
        )
        for column_name in context.table.c.keys()
        if column_name.endswith(DERIVED_SUFFIXES) and "denormalized" not in designed_columns.get(column_name, {})
    ]


def _check_foreign_keys(context: TableContext) -> list[Violation]:
    """FK 에 ondelete 명시"""
    return [
        context.violation("schema-fk-ondelete", f"{column.name} FK 에 ondelete 누락", MODEL_DOC)
        for column in context.table.c
        for foreign_key in column.foreign_keys
        if not foreign_key.ondelete
    ]


def _check_primary_key(context: TableContext) -> list[Violation]:
    """단일 integer PK (연결 테이블은 복합 PK 허용)"""
    primary_columns = list(context.table.primary_key.columns)
    if context.is_association and primary_columns:
        return []
    if len(primary_columns) == 1 and _type_name(primary_columns[0]) == "integer":
        return []
    return [context.violation("schema-integer-pk", "PK 는 단일 integer autoincrement 컬럼(id)", MODEL_DOC)]


def _check_timestamps(context: TableContext) -> list[Violation]:
    """created_at / updated_at 필수 (연결 테이블 제외)"""
    if context.is_association:
        return []
    return [
        context.violation("schema-timestamps", f"{column_name} 컬럼 누락", MODEL_DOC)
        for column_name in TIMESTAMP_COLUMNS
        if column_name not in context.table.c
    ]


def _check_table_naming(context: TableContext) -> list[Violation]:
    """일반 테이블은 복수형 snake_case"""
    last_word = context.table.name.split("_")[-1]
    if context.is_association or last_word.endswith("s") or last_word in IRREGULAR_PLURALS:
        return []
    return [context.violation("schema-plural-table", "테이블명은 복수형 snake_case (예: posts)", MODEL_DOC)]


def _check_unnamed_unique(context: TableContext) -> list[Violation]:
    """여러 컬럼 UniqueConstraint 는 uq_* 이름 필수"""
    return [
        context.violation("schema-unnamed-unique", "이름 없는 UniqueConstraint — name='uq_...' 지정", MODEL_DOC)
        for constraint in context.table.constraints
        if isinstance(constraint, UniqueConstraint) and len(constraint.columns) > 1 and not constraint.name
    ]


TABLE_CHECKS = [
    _check_repeating_columns,
    _check_list_columns,
    _check_copied_columns,
    _check_derived_columns,
    _check_foreign_keys,
    _check_primary_key,
    _check_timestamps,
    _check_table_naming,
    _check_unnamed_unique,
]


def _check_normalization(design: dict[str, DesignedTable], sources: dict[str, TableSource]) -> list[Violation]:
    """모든 테이블에 정규화·규약 검사 적용"""
    found: list[Violation] = []
    for name, table in sorted(Base.metadata.tables.items()):
        context = TableContext(table, sources.get(name, TableSource("app/domains", 0)), design.get(name))
        for check in TABLE_CHECKS:
            found += check(context)
    return found


# ---------- 3. 테이블 간 (중복 의심·미사용) ----------


def _foreign_key_targets(table: Table) -> frozenset[str]:
    """이 테이블이 가리키는 테이블 이름 집합"""
    return frozenset(foreign_key.column.table.name for column in table.c for foreign_key in column.foreign_keys)


def _column_signature(table: Table) -> set[tuple[str, str]]:
    """id·타임스탬프를 뺀 (컬럼명, 타입) 집합 — 테이블 '모양' 비교용"""
    return {(column.name, _type_name(column)) for column in table.c if column.name not in {"id", *TIMESTAMP_COLUMNS}}


def _is_declared_distinct(design: dict[str, DesignedTable], first: str, second: str) -> bool:
    """data-model.yaml 에 두 테이블을 따로 두는 사유가 적혀 있는가 (어느 쪽에 적어도 됨)"""
    first_design, second_design = design.get(first), design.get(second)
    return bool(
        (first_design and second in first_design.distinct_from)
        or (second_design and first in second_design.distinct_from)
    )


def _are_similar(first: Table, second: Table) -> bool:
    """FK 대상이 같고 (컬럼명, 타입) 겹침이 SIMILAR_TABLE_RATIO 이상"""
    targets = _foreign_key_targets(first)
    if not targets or targets != _foreign_key_targets(second):
        return False
    first_signature, second_signature = _column_signature(first), _column_signature(second)
    union = first_signature | second_signature
    return bool(union) and len(first_signature & second_signature) / len(union) >= SIMILAR_TABLE_RATIO


def _check_similar_tables(
    tables: dict[str, Table], design: dict[str, DesignedTable], sources: dict[str, TableSource]
) -> list[Violation]:
    """모양이 거의 같은 테이블 쌍 — 하나로 합칠 수 있는지(종류 enum) 먼저 검토하게 한다"""
    found: list[Violation] = []
    names = sorted(tables)
    for index, first in enumerate(names):
        for second in names[index + 1 :]:
            if _is_declared_distinct(design, first, second) or not _are_similar(tables[first], tables[second]):
                continue
            source = sources.get(second, TableSource("app/domains", 0))
            detail = (
                f"{second}: {first} 와 모양이 거의 같음 — 종류(enum) 컬럼으로 합칠 수 있는지 검토, "
                f"따로 둬야 하면 data-model.yaml 에 distinct_from: {{{first}: 사유}}"
            )
            found.append(Violation(source.file, source.line, "schema-similar-tables", detail, DESIGN_DOC))
    return found


def _referenced_names(path: Path) -> set[str]:
    """파일 안에서 쓰인 이름·속성·문자열 상수 (relationship("Post") 같은 문자열 참조 포함)"""
    referenced: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Name):
            referenced.add(node.id)
        elif isinstance(node, ast.Attribute):
            referenced.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            referenced.add(node.value)
    return referenced


def _app_referenced_names(app_dir: Path = APP_DIR) -> set[str]:
    """app/ 전체에서 참조된 이름 (클래스 정의 자체는 ClassDef 라 포함되지 않는다)"""
    referenced: set[str] = set()
    for path in app_dir.rglob("*.py"):
        referenced |= _referenced_names(path)
    return referenced


def _check_unused_tables(
    design: dict[str, DesignedTable], sources: dict[str, TableSource], referenced: set[str]
) -> list[Violation]:
    """앱 코드 어디에서도 모델 클래스를 쓰지 않는 테이블 (연결 테이블은 relationship 이 쓰므로 제외)"""
    return [
        Violation(
            source.file,
            source.line,
            "schema-unused-table",
            f"{name}: 모델 {source.class_name} 을 쓰는 코드가 없음 — "
            "필요 없으면 정리(schema-cleanup), 곧 쓸 예정이면 그 Task 와 함께 추가",
            DESIGN_DOC,
        )
        for name, source in sorted(sources.items())
        if source.class_name
        and not (name in design and design[name].is_association)
        and source.class_name not in referenced
    ]


def unused_table_report() -> list[Violation]:
    """주간 점검용 — 미사용 테이블 (scripts/gc/check.sh 가 호출, 커밋 차단 아님)"""
    return _check_unused_tables(_load_design(), _load_table_sources(), _app_referenced_names())


# ---------- 4. alembic 등록 ----------


def _alembic_imported_modules() -> set[str]:
    """alembic/env.py 가 import 하는 모듈"""
    tree = ast.parse(ALEMBIC_ENV_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def _check_alembic_registration() -> list[Violation]:
    """도메인 models 가 alembic/env.py 에 등록됐는지"""
    imported = _alembic_imported_modules()
    return [
        Violation(
            "alembic/env.py",
            0,
            "schema-alembic-registered",
            f"app.domains.{domain}.models 미등록 — import 해야 마이그레이션이 생성된다",
            MODEL_DOC,
        )
        for domain in _domain_model_modules()
        if f"app.domains.{domain}.models" not in imported
    ]


# ---------- 수집 ----------


def collect_violations() -> list[Violation]:
    """스키마 위반 전체 수집"""
    sources = _load_table_sources()
    raw_document = yaml.safe_load(DATA_MODEL_PATH.read_text(encoding="utf-8")) or {}
    design = _load_design()
    return (
        _validate_design(raw_document.get("tables") or {}, design)
        + _check_design_match(design, sources)
        + _check_normalization(design, sources)
        + _check_similar_tables(dict(Base.metadata.tables), design, sources)
        + _check_alembic_registration()
    )


def test_no_new_schema_violations() -> None:
    """known-violations.json 에 없는 새 스키마 위반이 없어야 한다"""
    new = new_violation_messages(collect_violations(), _is_schema_rule)
    assert not new, "새 DB 스키마 위반:\n" + "\n".join(new)


def test_known_schema_violations_only_shrink() -> None:
    """고쳐진 스키마 위반은 known-violations.json 에서 삭제해야 한다 (래칫)"""
    stale = stale_known_keys(collect_violations(), _is_schema_rule)
    assert not stale, STALE_MESSAGE + "\n".join(stale)


def test_data_model_file_exists() -> None:
    """설계 문서가 있어야 한다"""
    assert Path(DATA_MODEL_PATH).exists(), f"{DATA_MODEL_FILE} 가 없다 — {DESIGN_DOC} 참고"
