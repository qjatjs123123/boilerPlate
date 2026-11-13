---
description: backend/app/domains/{domain}/schemas.py — Pydantic Request/Response DTO 작성 또는 수정 시
paths:
  - "backend/app/domains/*/schemas.py"
---

# Schema Layer — Pydantic DTO 규칙

`app/domains/{domain}/schemas.py` 는 **API 입출력 계약 전용** 계층. 요청 검증과 응답 직렬화만 담당한다.
공통 코딩 규칙(네이밍·포맷팅·import·주석)은 `python-convention.md` — 기준은 `docs/backend/CONVENTIONS.md`.

---

## 네이밍

| 용도 | 클래스명 (`PascalCase`) | 예 |
|---|---|---|
| 생성 요청 | `{Entity}CreateRequest` | `PostCreateRequest` |
| 수정 요청 | `{Entity}UpdateRequest` | `PostUpdateRequest` |
| 단건 응답 | `{Entity}Response` | `PostResponse` |
| 목록 아이템 (필드 축소) | `{Entity}SummaryResponse` | `PostSummaryResponse` |
| 중첩 표현 | `{Entity}Summary` | `AuthorSummary` |

- 필드명은 **`snake_case`, 약어 없이** — `cover_image_url` (`img` ❌). 백엔드가 계약의 원본이고 camelCase 변환은 프론트 담당.
- Boolean 필드는 `is_` / `has_` 접두사 — 모델 컬럼명과 동일하게 (`is_published`).
- 커스텀 검증 메서드는 `validate_{필드}` — `validate_tags`.
- 목록 전체 응답 스키마는 만들지 않는다 — `paginate()`/`cursor_page()`(`app/common/pagination.py`)가 `{results, pagination}` 를 조립한다.

## 핵심 원칙

1. **엔티티를 응답으로 직접 노출 금지** — 라우터에서 `PostResponse.model_validate(post)` 경유.
2. **Response 계열은 `model_config = ConfigDict(from_attributes=True)`**.
3. **제약은 `Field(...)` 로 선언** — `min_length`, `max_length`, `ge`, `le`. 라우터·서비스의 수동 길이 검사 금지.
4. **길이·개수 제약값은 상수** — 모델과 같은 값이면 모델 모듈의 상수를 import 해 재사용 (`TITLE_MAX_LENGTH`). 매직 넘버 반복 금지.
5. **UpdateRequest 는 전 필드 Optional** (`X | None = None`) — service 가 `model_dump(exclude_unset=True)`. **보내지 않은 필드 = 변경 없음, `null` = 값 비우기**이므로, 모델에서 NOT NULL 인 컬럼 필드는 `validate_not_null` 로 명시적 `null` 을 422 로 막는다 (안 막으면 DB 에서 500 — `api-spec` 스킬 「PATCH 의 null 의미」).
6. **커스텀 검증은 `field_validator`, 교차 필드는 `model_validator`** — 형식 검증까지만. 존재·중복·권한 등 DB 검증은 service.
7. **검증 에러 메시지는 한국어** — 메시지 문자열은 모듈 상단 상수로.
8. **Request·Response 공용 금지** — 역할이 다르면 클래스를 나눈다. 같은 필드 묶음이 반복되면 `_` 접두 베이스 클래스로 공통화(코드 반복 최소화).
9. 민감 정보(비밀번호 해시 등)는 Response 에 넣지 않는다.
10. 리스트 기본값은 `Field(default_factory=list)` — 뮤터블 기본값 금지.

## 템플릿

> 아래 `Post` 는 규칙을 보여 주기 위한 **설명용 예시**다 (`slug`·`tags`·`like_count` 등 실제 테이블에 없는 필드 포함). 실제 컬럼은 `backend/data-model.yaml` 이 단일 출처이고, 구현 예는 `backend/app/domains/post/` 를 본다.

```python
# app/domains/post/schemas.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domains.post.models import TITLE_MAX_LENGTH

MAX_TAG_COUNT = 10
TAG_MAX_LENGTH = 30
TAG_TOO_LONG_MESSAGE = f"태그는 {TAG_MAX_LENGTH}자 이하여야 합니다."
NOT_NULL_MESSAGE = "비울 수 없는 항목입니다."


class AuthorSummary(BaseModel):
    """응답에 중첩되는 작성자 요약"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class PostCreateRequest(BaseModel):
    """POST /api/posts 요청 본문"""

    title: str = Field(..., min_length=1, max_length=TITLE_MAX_LENGTH)
    content: str = Field(..., min_length=1)
    is_published: bool = False
    tags: list[str] = Field(default_factory=list, max_length=MAX_TAG_COUNT)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        """태그 길이 제한 — 앞뒤 공백 제거 후 검사"""
        stripped_tags = [tag.strip() for tag in tags]
        if any(len(tag) > TAG_MAX_LENGTH for tag in stripped_tags):
            raise ValueError(TAG_TOO_LONG_MESSAGE)
        return stripped_tags


class PostUpdateRequest(BaseModel):
    """PATCH /api/posts/{post_id} 요청 본문 — 보낸 필드만 수정"""

    title: str | None = Field(None, min_length=1, max_length=TITLE_MAX_LENGTH)
    content: str | None = Field(None, min_length=1)
    is_published: bool | None = None
    tags: list[str] | None = Field(None, max_length=MAX_TAG_COUNT)

    @field_validator("title", "content", "is_published", "tags")
    @classmethod
    def validate_not_null(cls, value: object) -> object:
        """NOT NULL 컬럼에 명시적 null 차단 — 기본값(미전송)에는 실행되지 않는다"""
        if value is None:
            raise ValueError(NOT_NULL_MESSAGE)
        return value


class PostResponse(BaseModel):
    """포스트 단건 응답"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    content: str
    is_published: bool
    published_at: datetime | None
    like_count: int
    author: AuthorSummary
    created_at: datetime
    updated_at: datetime


class PostSummaryResponse(BaseModel):
    """포스트 목록 아이템 — 본문 제외"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    like_count: int
    author: AuthorSummary
    created_at: datetime
```

> 스키마 모듈은 상수를 쓰려고 **같은 도메인의** models 모듈 상수만 import 할 수 있다. 모델 클래스 자체를 타입으로 쓰지는 않는다.

---

## 체크리스트

- [ ] 클래스명이 네이밍 표(`CreateRequest`/`UpdateRequest`/`Response`/`SummaryResponse`/`Summary`) 준수?
- [ ] 필드명 snake_case·약어 없음, Boolean `is_`/`has_`?
- [ ] Response 계열 `from_attributes=True`?
- [ ] 제약이 전부 `Field(...)` + 상수값?
- [ ] UpdateRequest 전 필드 Optional?
- [ ] 검증 메시지 한국어 + 상수?
- [ ] DB 필요한 검증이 스키마에 없음?

## 금지 사항

- ❌ 라우터가 엔티티·dict 를 그대로 반환
- ❌ Request/Response 스키마 공용
- ❌ 스키마 안에서 DB 세션·repository 접근
- ❌ camelCase 필드명, 약어 필드명
- ❌ `Field(max_length=255)` 같은 매직 넘버 반복
- ❌ `tags: list[str] = []` (뮤터블 기본값)
