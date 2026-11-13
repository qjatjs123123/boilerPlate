from pydantic import BaseModel

from scripts.check_contract import SpecEndpoint, compare, parse_endpoints

SPEC_LINES = """
인증 헤더 규칙은 공통 절을 따른다.

### GET /api/items

- **응답 형태**: 목록(페이지) — `results` 아이템: `ItemResponse`
- **파라미터**:

| 이름 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| page | query | int | ❌ | 1 | 페이지 |
| X-User-Id | header | string | ❌ | 없음 | 인증 |

- **Response `data.results[]`** (`ItemResponse`):

| 필드 | 타입 | nullable | 설명 |
|---|---|---|---|
| id | int | ❌ | |
| name | string | ❌ | |

- **에러**:

| code | 조건 | message |
|---|---|---|
| 422 | 범위 밖 | 입력값이 올바르지 않습니다. (fields: `query.page`) |

### POST /api/items/{item_id}/views

- **응답 형태**: 동작 (200) — `ItemViewResponse`
- **파라미터**: 없음
""".splitlines()


class ItemResponse(BaseModel):
    """테스트용 응답 스키마"""

    id: int
    name: str


OPENAPI = {
    "paths": {
        "/api/items": {
            "get": {
                "parameters": [
                    {"name": "page", "in": "query"},
                    {"name": "X-User-Id", "in": "header"},
                ],
                "responses": {"200": {}, "422": {}},
            }
        }
    }
}
CODE = 'VALIDATION_MESSAGE = "입력값이 올바르지 않습니다."'


def test_parse_endpoints_reads_parameters_status_fields_and_messages() -> None:
    """엔드포인트별 query·path 파라미터(header 제외)·status·응답 필드·에러 message 를 읽는다"""
    endpoints = parse_endpoints(SPEC_LINES)

    assert [(endpoint.method, endpoint.path) for endpoint in endpoints] == [
        ("GET", "/api/items"),
        ("POST", "/api/items/{item_id}/views"),
    ]
    listing, view = endpoints
    assert listing.parameter_names == {"page"}
    assert listing.schema_fields == {"ItemResponse": {"id", "name"}}
    assert listing.error_messages == ["입력값이 올바르지 않습니다."]
    assert view.status_code == "200"
    assert view.parameter_names == set()


def test_compare_when_contract_matches_returns_empty() -> None:
    """파라미터·필드·message 가 모두 같으면 불일치 없음"""
    listing = parse_endpoints(SPEC_LINES)[0]

    assert compare(listing, OPENAPI, {"ItemResponse": ItemResponse}, CODE) == []


def test_compare_reports_missing_endpoint() -> None:
    """실제 서버에 없는 엔드포인트를 알린다"""
    view = parse_endpoints(SPEC_LINES)[1]

    assert compare(view, OPENAPI, {}, CODE) == ["POST /api/items/{item_id}/views: 실제 서버에 없는 엔드포인트"]


def test_compare_reports_parameter_field_and_message_differences() -> None:
    """파라미터 이름·응답 필드·에러 message 가 다르면 각각 알린다"""
    endpoint = SpecEndpoint(
        method="GET",
        path="/api/items",
        parameter_names={"page", "sort"},
        schema_fields={"ItemResponse": {"id", "title"}},
        error_messages=["없는 메시지"],
    )

    problems = compare(endpoint, OPENAPI, {"ItemResponse": ItemResponse}, CODE)

    assert len(problems) == 3
    assert "파라미터" in problems[0]
    assert "ItemResponse 필드" in problems[1]
    assert "없는 메시지" in problems[2]
