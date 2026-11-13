"""실행 중인 서버에 요청 1건을 보내 응답 envelope 형식을 확인한다 — backend/verify 스킬용 (jq 없이 동작)

사용 예 (레포 루트에서):
    backend/.venv/bin/python backend/scripts/check_envelope.py GET /api/posts --expect success --list page
    backend/.venv/bin/python backend/scripts/check_envelope.py GET /api/posts/999999 --expect fail --code 404
    backend/.venv/bin/python backend/scripts/check_envelope.py POST /api/posts --json '{}' --expect fail --code 422
    backend/.venv/bin/python backend/scripts/check_envelope.py POST /api/posts --header X-User-Id:1 --json '{...}' \
        --expect success --code 201

통과하면 exit 0, 아니면 이유를 출력하고 exit 1.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT_SECONDS = 10
PAGE_PAGINATION_KEYS = {"current_page", "num_pages", "page_size", "total_count", "has_previous", "has_next"}
CURSOR_PAGINATION_KEYS = {"next_cursor", "has_next"}


def parse_arguments() -> argparse.Namespace:
    """명령줄 인자 — 메서드·경로·기대 envelope"""
    parser = argparse.ArgumentParser(description="응답 envelope 형식 확인")
    parser.add_argument("method", choices=["GET", "POST", "PUT", "PATCH", "DELETE"])
    parser.add_argument("path", help="/api/... 경로")
    parser.add_argument("--expect", required=True, choices=["success", "fail", "error"])
    parser.add_argument("--code", type=int, help="기대 HTTP status (생략 시 확인 안 함)")
    parser.add_argument("--list", choices=["page", "cursor"], help="목록 응답이면 pagination 형태")
    parser.add_argument("--json", help="요청 body (JSON 문자열)")
    parser.add_argument("--header", action="append", default=[], help="추가 헤더 'Name:Value' (여러 번 가능)")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    return parser.parse_args()


def send_request(arguments: argparse.Namespace) -> tuple[int, dict[str, object]]:
    """요청을 보내고 (status, JSON body) 반환 — 4xx·5xx 도 body 를 읽는다"""
    body = arguments.json.encode() if arguments.json is not None else None
    request = urllib.request.Request(arguments.base_url + arguments.path, data=body, method=arguments.method)
    request.add_header("Content-Type", "application/json")
    for header in arguments.header:
        name, _, value = header.partition(":")
        request.add_header(name.strip(), value.strip())
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as exception:
        return exception.code, json.loads(exception.read() or b"null")


def find_problems(status: int, payload: object, arguments: argparse.Namespace) -> list[str]:
    """기대와 다른 점 목록 — 비어 있으면 통과"""
    if not isinstance(payload, dict) or set(payload) != {"status", "data"}:
        return [f"envelope 아님 (키가 status·data 두 개여야 함): {payload!r}"]
    problems = []
    if arguments.code is not None and status != arguments.code:
        problems.append(f"HTTP {status} — 기대 {arguments.code}")
    if payload["status"] != arguments.expect:
        problems.append(f"status '{payload['status']}' — 기대 '{arguments.expect}'")
    if arguments.expect == "success":
        problems += find_list_problems(payload["data"], arguments.list)
    else:
        problems += find_error_problems(payload["data"], status)
    return problems


def find_list_problems(data: object, list_kind: str | None) -> list[str]:
    """목록 응답의 results·pagination 형태 확인"""
    if list_kind is None:
        return []
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        return ["data.results 목록 없음"]
    expected_keys = PAGE_PAGINATION_KEYS if list_kind == "page" else CURSOR_PAGINATION_KEYS
    pagination = data.get("pagination")
    if not isinstance(pagination, dict) or set(pagination) != expected_keys:
        return [f"data.pagination 키가 {sorted(expected_keys)} 와 다름: {pagination!r}"]
    return []


def find_error_problems(data: object, status: int) -> list[str]:
    """fail·error 응답의 code·message 확인"""
    if not isinstance(data, dict):
        return ["data 가 객체가 아님"]
    problems = []
    if data.get("code") != status:
        problems.append(f"data.code {data.get('code')} — HTTP status {status} 와 다름")
    if not isinstance(data.get("message"), str) or not data["message"]:
        problems.append("data.message 비어 있음")
    if status == 422 and not data.get("fields"):
        problems.append("422 인데 data.fields 없음")
    return problems


def main() -> int:
    """요청 1건 검사 후 결과 출력"""
    arguments = parse_arguments()
    try:
        status, payload = send_request(arguments)
    except (urllib.error.URLError, json.JSONDecodeError) as exception:
        print(f"❌ {arguments.method} {arguments.path} — 요청 실패 또는 JSON 아님: {exception}")
        return 1
    problems = find_problems(status, payload, arguments)
    if problems:
        print(f"❌ {arguments.method} {arguments.path} — HTTP {status}")
        for problem in problems:
            print(f"   - {problem}")
        return 1
    print(f"✅ {arguments.method} {arguments.path} — HTTP {status} {arguments.expect} envelope OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
