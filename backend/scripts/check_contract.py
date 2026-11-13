"""spec 「API 설계」(화면이 믿고 만든 계약) ↔ 실제 백엔드 코드를 기계적으로 대조한다 — vibe-build 9단계용

사용 예 (레포 루트에서):
    backend/.venv/bin/python backend/scripts/check_contract.py spec/backend/002-board-extend.md

대조 항목 (spec 에 적힌 것만 — 표가 없는 엔드포인트 블록은 그 항목을 건너뛴다):
    - 엔드포인트(메서드 + 경로)가 app.openapi() 에 있는가
    - 파라미터 표의 query·path 이름 집합 == 실제 파라미터 이름 집합 (header 제외)
    - 응답 형태의 status (예: "(201)") 가 실제 응답 코드에 있는가
    - Response 표의 필드 이름 집합 == 스키마(`{Name}`)의 필드 이름 집합
    - 에러 표의 message 가 백엔드 코드(app/**)에 글자 그대로 있는가

전부 같으면 exit 0, 하나라도 다르면 목록을 출력하고 exit 1.
"""

import importlib
import os
import pkgutil
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

ENDPOINT_PATTERN = re.compile(r"^### (GET|POST|PUT|PATCH|DELETE) (/\S+)")
SCHEMA_NAME_PATTERN = re.compile(r"^- \*\*Response `data[^`]*`\*\* \(`(\w+)`\)")
STATUS_PATTERN = re.compile(r"^- \*\*응답 형태\*\*:.*\((\d{3})\)")
TABLE_ROW_PATTERN = re.compile(r"^\|(.+)\|\s*$")
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


@dataclass
class SpecEndpoint:
    """spec 의 엔드포인트 블록 하나에서 읽은 계약"""

    method: str
    path: str
    parameter_names: set[str] | None = None
    status_code: str | None = None
    schema_fields: dict[str, set[str]] = field(default_factory=dict)
    error_messages: list[str] = field(default_factory=list)


def read_api_section(spec_path: Path) -> list[str]:
    """spec 에서 「### API 설계」부터 다음 `## ` 장까지의 줄"""
    lines = spec_path.read_text(encoding="utf-8").splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == "### API 설계"), None)
    if start is None:
        sys.exit(f"❌ {spec_path}: 「### API 설계」 섹션이 없다")
    end = next((index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")), len(lines))
    return lines[start + 1 : end]


def table_rows_after(lines: list[str], start: int) -> list[list[str]]:
    """start 이후 처음 나오는 표의 본문 행 (머리글·구분선 제외)"""
    rows: list[list[str]] = []
    index = start + 1
    while index < len(lines) and not TABLE_ROW_PATTERN.match(lines[index]):
        if lines[index].startswith("- **") or lines[index].startswith("###"):
            return rows
        index += 1
    for line in lines[index + 2 :]:
        match = TABLE_ROW_PATTERN.match(line)
        if match is None:
            break
        rows.append([cell.strip() for cell in match.group(1).split("|")])
    return rows


def strip_code(cell: str) -> str:
    """`code` 표기와 굵게 표기를 벗긴 셀 값"""
    return cell.replace("`", "").replace("**", "").strip()


def parse_endpoints(lines: list[str]) -> list[SpecEndpoint]:
    """API 설계 섹션 → 엔드포인트 계약 목록"""
    endpoints: list[SpecEndpoint] = []
    for index, line in enumerate(lines):
        if match := ENDPOINT_PATTERN.match(line):
            endpoints.append(SpecEndpoint(method=match.group(1), path=match.group(2)))
            continue
        if not endpoints:
            continue
        endpoint = endpoints[-1]
        if line.startswith("- **파라미터**") and "없음" not in line:
            rows = table_rows_after(lines, index)
            endpoint.parameter_names = {strip_code(row[0]) for row in rows if strip_code(row[1]) in ("query", "path")}
        elif line.startswith("- **파라미터**"):
            endpoint.parameter_names = set()
        elif status_match := STATUS_PATTERN.match(line):
            endpoint.status_code = status_match.group(1)
        elif schema_match := SCHEMA_NAME_PATTERN.match(line):
            rows = table_rows_after(lines, index)
            endpoint.schema_fields[schema_match.group(1)] = {strip_code(row[0]) for row in rows}
        elif line.startswith("- **에러**"):
            for row in table_rows_after(lines, index):
                message = strip_code(row[2]).split(" (fields")[0].strip()
                if message:
                    endpoint.error_messages.append(message)
    return endpoints


def load_schema_classes() -> dict[str, type[BaseModel]]:
    """app/domains/*/schemas.py 의 Pydantic 모델을 이름으로 모은다"""
    import app.domains as domains_package

    schema_classes: dict[str, type[BaseModel]] = {}
    for module_info in pkgutil.iter_modules(domains_package.__path__):
        try:
            module = importlib.import_module(f"app.domains.{module_info.name}.schemas")
        except ModuleNotFoundError:
            continue
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, BaseModel) and value is not BaseModel:
                schema_classes[value.__name__] = value
    return schema_classes


def load_code_text() -> str:
    """에러 message 대조용 — 백엔드 app/ 아래 모든 파이썬 코드"""
    return "\n".join(path.read_text(encoding="utf-8") for path in (BACKEND_DIR / "app").rglob("*.py"))


def compare(endpoint: SpecEndpoint, openapi: dict, schema_classes: dict[str, type[BaseModel]], code: str) -> list[str]:
    """엔드포인트 하나의 불일치 목록"""
    label = f"{endpoint.method} {endpoint.path}"
    operation = openapi["paths"].get(endpoint.path, {}).get(endpoint.method.lower())
    if operation is None:
        return [f"{label}: 실제 서버에 없는 엔드포인트"]
    problems: list[str] = []
    if endpoint.parameter_names is not None:
        actual = {param["name"] for param in operation.get("parameters", []) if param["in"] in ("query", "path")}
        if actual != endpoint.parameter_names:
            problems.append(f"{label}: 파라미터 — spec {sorted(endpoint.parameter_names)} / 실제 {sorted(actual)}")
    if endpoint.status_code is not None and endpoint.status_code not in operation["responses"]:
        problems.append(f"{label}: status — spec {endpoint.status_code} / 실제 {sorted(operation['responses'])}")
    for schema_name, spec_fields in endpoint.schema_fields.items():
        schema_class = schema_classes.get(schema_name)
        if schema_class is None:
            problems.append(f"{label}: 스키마 {schema_name} 가 코드에 없음")
            continue
        actual_fields = set(schema_class.model_fields)
        if actual_fields != spec_fields:
            problems.append(f"{label}: {schema_name} 필드 — spec {sorted(spec_fields)} / 실제 {sorted(actual_fields)}")
    for message in endpoint.error_messages:
        if f'"{message}"' not in code:
            problems.append(f'{label}: 에러 message "{message}" 가 코드에 없음')
    return problems


def main() -> int:
    """spec 경로를 받아 대조 결과를 출력한다"""
    if len(sys.argv) != 2:
        sys.exit("사용법: check_contract.py spec/backend/{NNN}-{기능}.md")
    spec_path = Path(sys.argv[1]).resolve()
    # 앱 설정(.env)은 backend/ 기준으로 읽히므로 어디서 실행해도 그 폴더로 옮긴 뒤 앱을 불러온다
    os.chdir(BACKEND_DIR)

    from app.main import app

    endpoints = parse_endpoints(read_api_section(spec_path))
    if not endpoints:
        sys.exit(f"❌ {spec_path}: API 설계에 엔드포인트(### METHOD /path)가 없다")
    openapi = app.openapi()
    schema_classes = load_schema_classes()
    code = load_code_text()

    problems = [problem for endpoint in endpoints for problem in compare(endpoint, openapi, schema_classes, code)]
    if problems:
        print(f"❌ 계약 불일치 {len(problems)}건 ({len(endpoints)}개 엔드포인트 대조)")
        for problem in problems:
            print(f"   - {problem}")
        return 1
    print(f"✅ 계약 일치 — {len(endpoints)}개 엔드포인트 (파라미터·status·응답 필드·에러 message)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
