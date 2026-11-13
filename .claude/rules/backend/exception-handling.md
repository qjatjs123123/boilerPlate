---
description: backend/app/domains/{domain}/exceptions.py 또는 app/common/ (예외·핸들러·envelope) 작성 또는 수정 시
paths:
  - "backend/app/domains/*/exceptions.py"
  - "backend/app/common/**/*.py"
---

# Exception Handling — 예외·응답 envelope 규칙

**이 문서가 응답 envelope 스펙의 단일 출처다.** 모든 API 응답은 아래 3형식 중 하나여야 한다.
공통 코딩 규칙(네이밍·포맷팅·import·주석)은 `python-convention.md` — 기준은 `docs/backend/CONVENTIONS.md`.

---

## 응답 envelope 스펙

```jsonc
// 성공 (2xx) — data 는 null 허용
{ "status": "success", "data": { ... } }

// 목록 성공 — 표준(페이지 번호)
{ "status": "success",
  "data": {
    "results": [ ... ],
    "pagination": {
      "current_page": 1, "num_pages": 5, "page_size": 20,
      "total_count": 93, "has_previous": false, "has_next": true
    } } }

// 목록 성공 — 커서 변형 (피드 전용: 최신/트렌딩)
{ "status": "success",
  "data": { "results": [ ... ],
            "pagination": { "next_cursor": "abc123", "has_next": true } } }

// 클라이언트 오류 (4xx) — fields 는 검증 오류일 때만 채운다
{ "status": "fail",
  "data": { "code": 404, "message": "게시글을 찾을 수 없습니다.", "fields": { } } }

// 서버 오류 (5xx)
{ "status": "error",
  "data": { "code": 500, "message": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요." } }
```

- envelope 키는 전부 `snake_case`.
- `code` 는 HTTP status code 와 같은 정수.
- `message` 는 **사용자에게 보여줄 수 있는 한국어 문장** (마침표로 끝낸다).
- 5xx `message` 에 내부 정보(스택, SQL, 파일 경로) 노출 금지.

## 네이밍

- 도메인 예외 클래스: `{Entity}{상황}Exception` `PascalCase` — `PostNotFoundException`, `PostForbiddenException`, `PostSlugDuplicateException`.
- 예외 인스턴스 변수: `exception` (`exc`, `e` ❌) — `except ValueError as exception:`.
- 핸들러 함수: `handle_{대상}` — `handle_app_exception`, `handle_validation_error`.
- 공통 메시지·상태 상수: `UPPER_SNAKE_CASE` 모듈 상단 — `INTERNAL_ERROR_MESSAGE`, `VALIDATION_ERROR_STATUS`.
- 내부 헬퍼는 `_` 접두사 — `_error_response`, `_collect_validation_fields`.

## 예외 계층

```python
# app/common/exceptions.py
class AppException(Exception):
    """도메인 예외 베이스 — 글로벌 핸들러가 envelope 로 변환"""

    status_code: int = 500
    message: str = "일시적인 오류가 발생했습니다."

    def __init__(
        self,
        message: str | None = None,
        fields: dict[str, list[str]] | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.fields = fields or {}
        super().__init__(self.message)
```

도메인 예외는 `domains/{domain}/exceptions.py` 에 **클래스 속성 선언형**. 상황당 1클래스, 메시지는 클래스 속성 한 곳에만 둔다(문자열 반복 금지):

```python
# app/domains/post/exceptions.py
from app.common.exceptions import AppException


class PostNotFoundException(AppException):
    status_code = 404
    message = "포스트를 찾을 수 없습니다."


class PostForbiddenException(AppException):
    status_code = 403
    message = "포스트에 대한 권한이 없습니다."


class PostSlugDuplicateException(AppException):
    status_code = 409
    message = "이미 존재하는 슬러그입니다."
```

> 클래스명·속성만으로 의미가 드러나므로 도메인 예외 클래스에는 docstring 을 달지 않는다(뻔한 주석 금지). 베이스·핸들러처럼 동작이 있는 코드는 docstring 필수.

## 글로벌 핸들러 매핑 (`app/common/handlers.py`)

| 예외 | 응답 |
|---|---|
| `AppException` | 4xx → `fail`, 5xx → `error`. `code`=status_code, `message`, `fields` |
| `RequestValidationError` | 422 `fail` + `fields` 에 `{필드: [메시지]}` |
| `StarletteHTTPException` | status 기준 `fail`/`error` (라우트 없음 404 등) |
| `Exception` (그 외 전부) | 500 `error` + `logger.exception()` — **원본 메시지 노출 금지** |

- `register_exception_handlers(app)` 하나로 4종 등록, `app/main.py` 에서 1회 호출.
- `fail`/`error` envelope 조립은 `_error_response()` 한 곳에서만 — 핸들러마다 dict 를 따로 만들지 않는다(코드 반복 최소화).
- status 판정은 상수와 비교 — `status_code < SERVER_ERROR_STATUS` 처럼 매직 넘버 대신 상수.

## 핵심 원칙

1. **예외 → 응답 변환은 글로벌 핸들러에서만** — 라우터·서비스의 try/except 로 에러 응답 조립 금지.
2. **service 는 `AppException` 서브클래스만 raise** — `HTTPException` 금지(전 레이어).
3. **도메인 예외는 상황당 1클래스** — `status_code`·`message` 클래스 속성.
4. **동적 메시지·fields 는 생성자 인자로** — `UserEmailDuplicateException(fields={"email": ["이미 사용 중입니다."]})`.
5. **500 은 반드시 `logger.exception` 으로 스택 기록**, 응답은 고정 메시지만.
6. 예외를 다시 던질 때는 원인을 잇는다 — `raise PostNotFoundException() from exception`.

## 테스트

- 위치: `tests/unit/common/test_handlers.py` — 임시 FastAPI 앱 + TestClient (DB 없음).
- 검증: ① `AppException`(404) → `fail` envelope ② 검증 실패 → 422 + `fields` ③ 미처리 예외 → 500 `error` + 고정 메시지(원본 메시지 미노출).

---

## 체크리스트

- [ ] 모든 에러 응답이 fail/error envelope?
- [ ] 도메인 예외가 `{Entity}{상황}Exception` + 클래스 속성 선언형?
- [ ] 메시지가 한국어 문장 + 한 곳에만 정의?
- [ ] `HTTPException` raise 0건?
- [ ] 예외 변수명 `exception` (약어 없음)?
- [ ] 500 응답에 내부 정보 없음 + `logger.exception`?
- [ ] `register_exception_handlers(app)` 가 main.py 에서 호출?
- [ ] `pytest tests/unit/common` 통과?

## 금지 사항

- ❌ 라우터·서비스에서 `JSONResponse` 로 에러 직접 조립
- ❌ envelope 3형식 외 응답 (`{"detail": ...}` FastAPI 기본형)
- ❌ `fail`(4xx) / `error`(5xx) 혼용
- ❌ 영어 사용자 메시지, 같은 메시지 문자열 복붙
- ❌ `except Exception: pass` (예외 삼키기)
- ❌ `except ... as e` / `as exc` 약어
