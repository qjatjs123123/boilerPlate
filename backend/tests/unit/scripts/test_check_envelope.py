from argparse import Namespace

from scripts.check_envelope import find_problems

PAGE_PAGINATION = {
    "current_page": 1,
    "num_pages": 1,
    "page_size": 20,
    "total_count": 0,
    "has_previous": False,
    "has_next": False,
}


def make_arguments(expect: str, code: int | None = None, list_kind: str | None = None) -> Namespace:
    """find_problems 가 읽는 인자만 채운 Namespace"""
    return Namespace(expect=expect, code=code, list=list_kind)


def test_find_problems_when_success_envelope_matches_returns_empty() -> None:
    """기대한 success envelope 이면 문제 없음"""
    payload = {"status": "success", "data": {"status": "ok"}}

    assert find_problems(200, payload, make_arguments("success", code=200)) == []


def test_find_problems_when_page_list_matches_returns_empty() -> None:
    """페이지형 목록의 results·pagination 키가 맞으면 문제 없음"""
    payload = {"status": "success", "data": {"results": [], "pagination": PAGE_PAGINATION}}

    assert find_problems(200, payload, make_arguments("success", list_kind="page")) == []


def test_find_problems_when_pagination_keys_differ_reports_problem() -> None:
    """커서형을 기대했는데 페이지형이 오면 문제로 보고"""
    payload = {"status": "success", "data": {"results": [], "pagination": PAGE_PAGINATION}}

    problems = find_problems(200, payload, make_arguments("success", list_kind="cursor"))

    assert len(problems) == 1
    assert "pagination" in problems[0]


def test_find_problems_when_not_envelope_reports_problem() -> None:
    """FastAPI 기본 {"detail": ...} 응답은 envelope 아님으로 보고"""
    problems = find_problems(404, {"detail": "Not Found"}, make_arguments("fail", code=404))

    assert len(problems) == 1
    assert "envelope" in problems[0]


def test_find_problems_when_fail_envelope_matches_returns_empty() -> None:
    """code·message 가 채워진 404 fail envelope 이면 문제 없음"""
    payload = {"status": "fail", "data": {"code": 404, "message": "찾을 수 없습니다.", "fields": {}}}

    assert find_problems(404, payload, make_arguments("fail", code=404)) == []


def test_find_problems_when_422_without_fields_reports_problem() -> None:
    """422 인데 fields 가 비어 있으면 문제로 보고"""
    payload = {"status": "fail", "data": {"code": 422, "message": "입력값이 올바르지 않습니다.", "fields": {}}}

    problems = find_problems(422, payload, make_arguments("fail", code=422))

    assert problems == ["422 인데 data.fields 없음"]


def test_find_problems_when_status_and_code_differ_reports_both() -> None:
    """HTTP status 와 envelope status 가 모두 기대와 다르면 둘 다 보고"""
    payload = {"status": "error", "data": {"code": 500, "message": "일시적인 오류가 발생했습니다."}}

    problems = find_problems(500, payload, make_arguments("success", code=200))

    assert any("HTTP 500" in problem for problem in problems)
    assert any("status 'error'" in problem for problem in problems)
