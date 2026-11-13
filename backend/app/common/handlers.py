import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.exceptions import AppException

logger = logging.getLogger("app")

INTERNAL_ERROR_MESSAGE = "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
VALIDATION_ERROR_MESSAGE = "입력값이 올바르지 않습니다."
VALIDATION_ERROR_STATUS = 422
SERVER_ERROR_STATUS = 500


def _error_response(
    status_code: int,
    message: str,
    fields: dict[str, list[str]] | None = None,
) -> JSONResponse:
    """status_code 기준 fail(4xx)/error(5xx) envelope 응답을 만든다"""
    status = "fail" if status_code < SERVER_ERROR_STATUS else "error"
    data: dict[str, object] = {"code": status_code, "message": message}
    if status == "fail":
        data["fields"] = fields or {}
    return JSONResponse(status_code=status_code, content={"status": status, "data": data})


def _collect_validation_fields(exception: RequestValidationError) -> dict[str, list[str]]:
    """RequestValidationError.errors()를 {필드: [메시지]}로 정리한다"""
    fields: dict[str, list[str]] = {}
    for error in exception.errors():
        loc = [str(part) for part in error.get("loc", ()) if part != "body"]
        field = ".".join(loc) or "body"
        fields.setdefault(field, []).append(error.get("msg", "invalid"))
    return fields


def register_exception_handlers(app: FastAPI) -> None:
    """전 예외 → envelope 변환 핸들러 4종을 등록한다 (main.py에서 1회 호출)"""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exception: AppException) -> JSONResponse:
        if exception.status_code >= SERVER_ERROR_STATUS:
            logger.exception("app_exception - path=%s", request.url.path, exc_info=exception)
        return _error_response(exception.status_code, exception.message, exception.fields)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exception: RequestValidationError) -> JSONResponse:
        return _error_response(VALIDATION_ERROR_STATUS, VALIDATION_ERROR_MESSAGE, _collect_validation_fields(exception))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exception: StarletteHTTPException) -> JSONResponse:
        message = str(exception.detail) if exception.detail else INTERNAL_ERROR_MESSAGE
        return _error_response(exception.status_code, message)

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exception: Exception) -> JSONResponse:
        logger.exception("unhandled_exception - path=%s", request.url.path)
        return _error_response(SERVER_ERROR_STATUS, INTERNAL_ERROR_MESSAGE)
