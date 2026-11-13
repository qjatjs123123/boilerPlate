"""아키텍처 경계 테스트 — .claude/rules/backend/*.md 의 금지 규칙을 AST로 기계 검증한다.

위반 메시지는 그대로 에이전트 컨텍스트가 된다: 무엇이·어디서·왜 위반인지 + 읽을 규칙 파일을 담는다.
기존 위반은 known-violations.json 에 기록하며 이 목록은 줄어들 수만 있다(래칫).
"""

import ast
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from tests.architecture._violations import (
    BACKEND_ROOT,
    RULES,
    STALE_MESSAGE,
    Violation,
    new_violation_messages,
    stale_known_keys,
)

DOMAINS_DIR = BACKEND_ROOT / "app" / "domains"
COMMON_DIR = BACKEND_ROOT / "app" / "common"


def _is_boundary_rule(rule: str) -> bool:
    """이 테스트가 소유한 규칙 — 스키마 규칙(schema-*)은 test_schema.py 소유"""
    return not rule.startswith("schema-")


def _imported_modules(tree: ast.AST) -> list[tuple[int, str, list[str]]]:
    """(줄, 모듈 경로, import 된 이름들) 목록 — 상대 import 는 '.' 접두로 표기"""
    found: list[tuple[int, str, list[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            found.append((node.lineno, module, [alias.name for alias in node.names]))
        elif isinstance(node, ast.Import):
            found.extend((node.lineno, alias.name, []) for alias in node.names)
    return found


def _method_calls(tree: ast.AST, names: set[str]) -> list[tuple[int, str]]:
    """obj.<name>(...) 형태 호출 중 names 에 해당하는 것"""
    return [
        (node.lineno, node.func.attr)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in names
    ]


def _other_domain(module: str, domain: str, layer: str) -> str | None:
    """app.domains.{other}.{layer} 를 import 하면 other 를 반환"""
    parts = module.split(".")
    if len(parts) == 4 and parts[:2] == ["app", "domains"] and parts[3] == layer and parts[2] != domain:
        return parts[2]
    return None


@dataclass(frozen=True)
class ImportRule:
    """레이어별 import 금지 규칙 1개"""

    layer: str  # "*" = 모든 레이어
    rule: str
    doc: str
    message: str  # {module}, {other} 치환
    matches: Callable[[str, list[str], str], str | None]  # (module, names, domain) → other 또는 "" / 미해당 None


def _when(cond: bool, other: str = "") -> str | None:
    """조건이 참이면 치환값, 아니면 None"""
    return other if cond else None


IMPORT_RULES = [
    ImportRule(
        "*",
        "no-http-exception",
        "exception-handling.md",
        "HTTPException 사용 금지 → 도메인 예외(AppException 서브클래스)를 raise",
        lambda m, n, d: _when("HTTPException" in n),
    ),
    ImportRule(
        "service",
        "service-no-fastapi",
        "service-layer.md",
        "service 가 {module} 를 import — service 는 프레임워크를 모른다",
        lambda m, n, d: _when(m.startswith("fastapi")),
    ),
    ImportRule(
        "service",
        "service-no-query",
        "service-layer.md",
        "service 에서 select 쿼리 작성 금지 → repository 메서드로",
        lambda m, n, d: _when(m.startswith("sqlalchemy") and "select" in n),
    ),
    ImportRule(
        "service",
        "service-no-cross-service",
        "service-layer.md",
        "다른 도메인 service({other}) 호출 금지 → 그 도메인 repository 를 주입",
        lambda m, n, d: _other_domain(m, d, "service"),
    ),
    ImportRule(
        "repository",
        "repository-no-schema",
        "repository-layer.md",
        "repository 가 스키마({module})를 import — 엔티티만 다룬다",
        lambda m, n, d: _when(m.endswith("schemas")),
    ),
    ImportRule(
        "repository",
        "repository-no-fastapi",
        "repository-layer.md",
        "repository 가 {module} 를 import",
        lambda m, n, d: _when(m.startswith("fastapi")),
    ),
    ImportRule(
        "router",
        "router-no-query",
        "router-layer.md",
        "router 에서 쿼리 작성 금지 → service → repository 경유",
        lambda m, n, d: _when(m.startswith("sqlalchemy") and "select" in n),
    ),
    ImportRule(
        "models",
        "models-no-cross-import",
        "model-layer.md",
        '다른 도메인 모델({other}) 직접 import 금지 → relationship("Name") 문자열 참조',
        lambda m, n, d: _other_domain(m, d, "models"),
    ),
    ImportRule(
        "models",
        "models-no-framework",
        "model-layer.md",
        "모델이 {module} 를 import (역방향 의존)",
        lambda m, n, d: _when(m.startswith(("fastapi", "pydantic"))),
    ),
    ImportRule(
        "schemas",
        "schemas-no-db",
        "schema-layer.md",
        "스키마가 {module} 에 의존 — 스키마는 형식 검증만",
        lambda m, n, d: _when(m.endswith(("repository", "service")) or "Session" in n),
    ),
]

# 레이어별 금지 메서드 호출: layer → (rule, doc, 금지 메서드)
CALL_RULES = {
    "repository": ("repository-no-commit-or-legacy", "repository-layer.md", {"commit", "rollback", "query"}),
    "router": ("router-no-db", "router-layer.md", {"query", "execute", "scalars", "commit"}),
}


def _import_violations(rel: str, tree: ast.AST, domain: str, layer: str) -> list[Violation]:
    """import 규칙 위반 수집"""
    found: list[Violation] = []
    rules = [r for r in IMPORT_RULES if r.layer in ("*", layer)]
    for line, module, names in _imported_modules(tree):
        for r in rules:
            other = r.matches(module, names, domain)
            if other is not None:
                detail = r.message.format(module=module, other=other)
                found.append(Violation(rel, line, r.rule, detail, f"{RULES}/{r.doc}"))
    return found


def _call_violations(rel: str, tree: ast.AST, layer: str) -> list[Violation]:
    """금지 메서드 호출 수집"""
    if layer not in CALL_RULES:
        return []
    rule, doc, names = CALL_RULES[layer]
    return [
        Violation(rel, line, rule, f"{layer} 에서 .{attr}() 직접 호출 금지", f"{RULES}/{doc}")
        for line, attr in _method_calls(tree, names)
    ]


def _check_domain_file(path: Path, domain: str, layer: str) -> list[Violation]:
    """도메인 레이어 파일 1개 검사"""
    rel = str(path.relative_to(BACKEND_ROOT))
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return _import_violations(rel, tree, domain, layer) + _call_violations(rel, tree, layer)


def _check_common() -> list[Violation]:
    """app/common 은 도메인을 몰라야 한다"""
    found: list[Violation] = []
    for path in COMMON_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for line, module, _ in _imported_modules(tree):
            if module.startswith("app.domains"):
                rel = str(path.relative_to(BACKEND_ROOT))
                detail = f"공통 모듈이 도메인({module})을 import — 의존 방향 역전"
                found.append(Violation(rel, line, "common-no-domain", detail, f"{RULES}/exception-handling.md"))
    return found


def collect_violations() -> list[Violation]:
    """전체 위반 수집"""
    found = _check_common()
    for domain_dir in sorted(p for p in DOMAINS_DIR.iterdir() if p.is_dir() and not p.name.startswith("_")):
        for path in sorted(domain_dir.glob("*.py")):
            found += _check_domain_file(path, domain_dir.name, path.stem)
    return found


def test_no_new_boundary_violations() -> None:
    """known-violations.json 에 없는 새 경계 위반이 없어야 한다"""
    new = new_violation_messages(collect_violations(), _is_boundary_rule)
    assert not new, "새 아키텍처 경계 위반:\n" + "\n".join(new)


def test_known_violations_only_shrink() -> None:
    """고쳐진 위반은 known-violations.json 에서 삭제해야 한다 (래칫)"""
    stale = stale_known_keys(collect_violations(), _is_boundary_rule)
    assert not stale, STALE_MESSAGE + "\n".join(stale)
