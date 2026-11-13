from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """성공 응답 envelope — {"status": "success", "data": ...}"""

    status: Literal["success"] = "success"
    data: T | None = None


def success_response(data: T | None = None) -> SuccessResponse[T]:
    """데이터를 success envelope로 감싼다"""
    return SuccessResponse[T](data=data)
