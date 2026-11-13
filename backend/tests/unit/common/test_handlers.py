from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.common.exceptions import AppException
from app.common.handlers import INTERNAL_ERROR_MESSAGE, register_exception_handlers


class SampleNotFoundException(AppException):
    status_code = 404
    message = "리소스를 찾을 수 없습니다."


class SamplePayload(BaseModel):
    title: str = Field(..., min_length=1)


def make_app() -> FastAPI:
    """핸들러가 등록된 임시 앱 (DB 불필요)"""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    def raise_not_found() -> None:
        raise SampleNotFoundException()

    @app.get("/boom")
    def raise_unhandled() -> None:
        raise RuntimeError("internal detail should not leak")

    @app.post("/validate")
    def validate(payload: SamplePayload) -> dict:
        return {"ok": True}

    return app


def test_app_exception_returns_fail_envelope() -> None:
    """AppException(4xx)은 fail envelope로 변환된다"""
    with TestClient(make_app()) as client:
        response = client.get("/not-found")

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "fail"
    assert body["data"]["code"] == 404
    assert body["data"]["message"] == "리소스를 찾을 수 없습니다."
    assert body["data"]["fields"] == {}


def test_validation_error_returns_fields() -> None:
    """RequestValidationError는 422 fail + fields로 변환된다"""
    with TestClient(make_app()) as client:
        response = client.post("/validate", json={})

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "fail"
    assert body["data"]["code"] == 422
    assert "title" in body["data"]["fields"]


def test_unhandled_exception_returns_error_envelope() -> None:
    """미처리 예외는 500 error envelope + 고정 메시지로 변환된다 (내부 정보 미노출)"""
    with TestClient(make_app(), raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "error"
    assert body["data"]["code"] == 500
    assert body["data"]["message"] == INTERNAL_ERROR_MESSAGE
    assert "internal detail" not in body["data"]["message"]
    assert "fields" not in body["data"]
