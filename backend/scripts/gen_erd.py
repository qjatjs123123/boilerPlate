"""data-model.yaml → docs/backend/ERD.md (Mermaid erDiagram) — 지금 DB 구조를 한 장의 그림으로 본다.

사용 예 (레포 루트에서):
    backend/.venv/bin/python backend/scripts/gen_erd.py          # ERD.md 다시 생성
    backend/.venv/bin/python backend/scripts/gen_erd.py --check  # 최신이 아니면 exit 1 (gc·검증용)

data-model.yaml 을 고칠 때마다(spec-run models Task) 다시 생성한다. ERD.md 는 손으로 고치지 않는다.
"""

import sys
from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_MODEL_PATH = BACKEND_DIR / "data-model.yaml"
ERD_PATH = BACKEND_DIR.parent / "docs" / "backend" / "ERD.md"

HEADER = """# ERD — 현재 DB 구조

> 자동 생성 파일 — 손으로 고치지 않는다. `backend/data-model.yaml` 을 고친 뒤
> `backend/.venv/bin/python backend/scripts/gen_erd.py` 로 다시 만든다.
> 개념(생활 언어) 설명은 `docs/backend/DOMAIN-MAP.md`.
"""


def _column_keys(spec: dict[str, object]) -> str:
    """PK·FK·UK 표시"""
    keys = [
        label
        for label, present in (
            ("PK", spec.get("primary_key")),
            ("FK", spec.get("foreign_key")),
            ("UK", spec.get("unique")),
        )
        if present
    ]
    return f" {', '.join(keys)}" if keys else ""


def _entity_lines(name: str, table: dict[str, object]) -> list[str]:
    """테이블 1개의 엔티티 블록"""
    lines = [f"    {name} {{"]
    for column_name, spec in (table.get("columns") or {}).items():
        spec = spec or {}
        lines.append(f"        {spec.get('type', 'unknown')} {column_name}{_column_keys(spec)}")
    lines.append("    }")
    return lines


def _relation_lines(name: str, table: dict[str, object]) -> list[str]:
    """FK 마다 '부모 ||--o{ 자식' 관계선 (unique FK 는 1:1, nullable FK 는 부모 없음 허용)"""
    lines: list[str] = []
    for column_name, spec in (table.get("columns") or {}).items():
        spec = spec or {}
        target = spec.get("foreign_key")
        if not target:
            continue
        parent_side = "|o" if spec.get("nullable", not spec.get("primary_key", False)) else "||"
        child_side = "o|" if spec.get("unique") else "o{"
        lines.append(f'    {str(target).split(".")[0]} {parent_side}--{child_side} {name} : "{column_name}"')
    return lines


def render(tables: dict[str, dict[str, object]]) -> str:
    """테이블 설계 → ERD.md 전체 내용"""
    entities: list[str] = []
    relations: list[str] = []
    for name, table in tables.items():
        entities += _entity_lines(name, table or {})
        relations += _relation_lines(name, table or {})
    body = ["```mermaid", "erDiagram", *relations, *entities, "```"]
    descriptions = [f"| `{name}` | {(table or {}).get('description', '')} |" for name, table in tables.items()]
    return "\n".join([HEADER, *body, "", "| 테이블 | 저장하는 것 |", "|---|---|", *descriptions, ""])


def main() -> int:
    tables = (yaml.safe_load(DATA_MODEL_PATH.read_text(encoding="utf-8")) or {}).get("tables") or {}
    content = render(tables)
    if "--check" in sys.argv[1:]:
        if not ERD_PATH.exists() or ERD_PATH.read_text(encoding="utf-8") != content:
            print("❌ docs/backend/ERD.md 가 data-model.yaml 과 다르다 → backend/scripts/gen_erd.py 실행")
            return 1
        print("✅ ERD 최신")
        return 0
    ERD_PATH.write_text(content, encoding="utf-8")
    print(f"✅ {ERD_PATH.relative_to(BACKEND_DIR.parent)} 생성 ({len(tables)}개 테이블)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
