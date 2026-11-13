import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PageParams:
    """페이지 번호 기반 쿼리 파라미터 (kebab-case alias) — Depends()로 주입"""

    def __init__(
        self,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(alias="page-size", ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        """SQL OFFSET 값"""
        return (self.page - 1) * self.page_size


@dataclass
class Page(Generic[T]):
    """service가 반환하는 페이지 결과 (엔티티 목록 + 메타)"""

    items: Sequence[T]
    total_count: int
    current_page: int
    page_size: int


def paginate(page: Page[T], schema: type[BaseModel]) -> dict[str, object]:
    """Page 결과를 표준 페이지 envelope data({results, pagination})로 조립한다"""
    num_pages = max(1, math.ceil(page.total_count / page.page_size))
    return {
        "results": [schema.model_validate(item) for item in page.items],
        "pagination": {
            "current_page": page.current_page,
            "num_pages": num_pages,
            "page_size": page.page_size,
            "total_count": page.total_count,
            "has_previous": page.current_page > 1,
            "has_next": page.current_page < num_pages,
        },
    }


def cursor_page(
    items: Sequence[object],
    next_cursor: str | None,
    schema: type[BaseModel],
) -> dict[str, object]:
    """피드 전용 커서 envelope data({results, pagination})를 조립한다"""
    return {
        "results": [schema.model_validate(item) for item in items],
        "pagination": {
            "next_cursor": next_cursor,
            "has_next": next_cursor is not None,
        },
    }
