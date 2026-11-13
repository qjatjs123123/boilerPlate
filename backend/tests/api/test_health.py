from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_success_envelope() -> None:
    """헬스 체크가 success envelope을 반환한다"""
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"] == {"status": "ok"}


def test_unknown_route_returns_fail_envelope() -> None:
    """없는 경로는 404 fail envelope을 반환한다"""
    with TestClient(app) as client:
        response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "fail"
    assert body["data"]["code"] == 404
    assert len(body["data"]["message"]) > 0
