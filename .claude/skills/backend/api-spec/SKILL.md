---
name: api-spec
description: API 엔드포인트를 설계하거나 명세(spec 의 API 섹션, 계약 문서)를 작성할 때 반드시 사용. 응답 형태(단건·페이지 목록·커서 목록·생성·삭제) 선택, HTTP 메서드·status code, 에러 코드표, 엔드포인트 명세 템플릿을 정한다.
---

# API 명세 규칙 — 엔드포인트 설계·문서화

**envelope 스펙의 단일 출처는 `.claude/rules/backend/exception-handling.md`** 다. 이 스킬은 envelope 를 다시 정의하지 않고, "어떤 엔드포인트에 어떤 응답 형태를 쓰고 어떻게 적는가"만 정한다.
작성한 명세는 구현 후 `backend/sync-api-docs` 가 만드는 `frontend/swagger/docs.md` 와 **같은 형식**이어야 한다. 설계(spec) → 구현 → 자동 생성 문서의 형식을 하나로 유지하기 위해서다.

---

## 1. 응답 형태 선택

| 상황 | 메서드 | status | `data` 형태 | 조립 함수 (`app/common/`) |
|---|---|---|---|---|
| 단건 조회 | `GET /api/{리소스}/{id}` | 200 | `{Entity}Response` | `success_response(...)` |
| 목록 (일반) | `GET /api/{리소스}` | 200 | `{results, pagination}` 페이지 번호형 | `paginate(page, {Entity}SummaryResponse)` |
| 목록 (피드: 최신·트렌딩·무한스크롤) | `GET /api/{리소스}/feed` 등 | 200 | `{results, pagination}` 커서형 | `cursor_page(items, next_cursor, schema)` |
| 생성 | `POST /api/{리소스}` | **201** | 생성된 `{Entity}Response` | `success_response(...)` |
| 부분 수정 | `PATCH /api/{리소스}/{id}` | 200 | 수정된 `{Entity}Response` | `success_response(...)` |
| 전체 교체 | `PUT /api/{리소스}/{id}` | 200 | 교체된 `{Entity}Response` | `success_response(...)` |
| 삭제 | `DELETE /api/{리소스}/{id}` | 200 | `null` | `success_response()` |
| 동작 켜기 (좋아요 등) | `POST /api/{리소스}/{id}/{동작}` | 200 | 변경 후 상태 요약 (예: `{"is_liked": true, "like_count": 3}`) | `success_response(...)` |
| 동작 끄기 (좋아요 취소 등) | `DELETE /api/{리소스}/{id}/{동작}` | 200 | 변경 후 상태 요약 (예: `{"is_liked": false, "like_count": 2}`) | `success_response(...)` |

- **204 No Content 를 쓰지 않는다** — 모든 응답은 envelope 를 가져야 하므로, 삭제도 `200 + data: null`.
- 목록은 **기본이 페이지 번호형**이다. 커서형은 피드에만 쓰고, 명세에 "커서형" 이라고 명시한다.
- 목록 아이템은 필드를 줄인 `{Entity}SummaryResponse` 를 기본으로 쓴다. 상세 필드(본문 등)가 목록에 꼭 필요할 때만 `{Entity}Response`.
- 페이지 파라미터는 `PageParams`(`page`, `page-size`, 기본 20, 최대 100)를 그대로 쓴다. 다른 기본값이 필요하면 명세에 이유를 적는다.
- **동작 엔드포인트는 멱등**이다 — 이미 좋아요한 상태에서 다시 `POST` 해도 에러(409)가 아니라 200 + 현재 상태. 화면에서 버튼을 두 번 눌러도 깨지지 않게 하기 위해서다.
  - **예외 — 누적 카운터**: 조회수처럼 "부를 때마다 1 늘리는 것"이 요구사항인 동작은 `POST /api/{리소스}/{id}/{동작}` 하나만 두고(끄기 없음) 비멱등을 허용한다. 명세에 "멱등 아님"과 증가 후 값을 적는다 (예: `POST /api/posts/{post_id}/views`).

### 목록 경계 동작 (`app/common/pagination.py` 기준)

- 범위 밖 페이지(`page` > `num_pages`)는 **404 가 아니라 200 + 빈 `results`**.
- 0건이면 `total_count: 0`, `num_pages: 1`, `results: []`.
- 커서(`next_cursor`)는 **불투명 문자열** — 프론트는 해석하지 않고 그대로 다음 요청에 넘긴다. 마지막 페이지면 `next_cursor: null`, `has_next: false`.

## 2. URL·파라미터 규칙

- 경로: `/api/{리소스 복수형 kebab-case}` — `/api/posts`, `/api/post-series/{series_id}`.
- 경로 파라미터: `snake_case` — `{post_id}`. ID 는 `int`.
- 동사를 URL 에 넣지 않는다 (`/api/posts/create` ❌). 단 CRUD 로 표현이 안 되는 동작만 하위 경로로 둔다 (`/api/posts/{post_id}/like`).
- 쿼리 파라미터: **kebab-case** — `page-size`, `search-keyword`.
- 정렬은 `sort` 하나에 **허용값 enum 문자열** — `sort=latest`, `sort=popular`. 허용값과 기본값을 파라미터 표 설명 칸에 모두 적는다. 허용값 밖이면 422.
- 필터는 필드별 쿼리 하나씩 — `category-id=3`, `is-published=true`. 검색어는 `search-keyword`.
- 요청·응답 body 필드: **snake_case**. Boolean 은 `is_`/`has_` 접두사.
- 날짜: **UTC 기준, 타임존 표기 없는 ISO8601** — `"2026-01-01T09:30:00.123456"` (모델이 `datetime.utcnow` 를 쓰므로 `Z` 가 붙지 않고 마이크로초가 붙을 수 있다). 프론트는 `models-layer.md` 의 `isoDatetime` 으로 받는다.
- 인증: 방식은 `backend/app/core/security.py` 가 기준이다. 현재는 **`X-User-Id` 헤더 스텁**(JWT 로 교체 예정) — 명세에 인증 방식을 따로 적지 않고 "인증" 항목만 적는다.

### PATCH 의 null 의미

- **보내지 않은 필드 = 변경 없음**, **`null` 을 보낸 필드 = 값 비우기**(service 의 `model_dump(exclude_unset=True)`).
- 그래서 DB 에서 비울 수 없는(NOT NULL) 필드는 PATCH 에서도 `null` 을 받으면 안 된다. 받으면 검증을 통과해 DB 에서 500 이 난다.
  → 명세 Request Body 표의 `nullable` 칸을 **모델 컬럼 기준**으로 적고, nullable ❌ 인 필드는 스키마에서 `null` 을 422 로 막는다.

## 3. 에러 코드표

엔드포인트마다 발생 가능한 에러를 표로 적는다. 메시지는 `domains/{domain}/exceptions.py` 의 클래스 속성과 **글자까지 같아야** 한다(명세가 먼저면 이 메시지로 예외 클래스를 만든다).

| code | 언제 | 예외 클래스 | 비고 |
|---|---|---|---|
| 400 | 형식은 맞지만 업무상 허용 안 되는 요청 | `{Entity}{상황}Exception` | 예: 이미 발행된 글 재발행 |
| 401 | 로그인 필요 엔드포인트에 인증 헤더 없음·존재하지 않는 사용자 | `UnauthorizedException` (`core/security.py`) | message "인증이 필요합니다." |
| 403 | 로그인했지만 권한 없음 (작성자 아님, staff 아님) | `{Entity}ForbiddenException` | |
| 404 | 대상 리소스 없음 | `{Entity}NotFoundException` | |
| 409 | 중복 (슬러그, 이메일 등 unique 값) | `{Entity}{상황}Exception` — 예: `PostSlugDuplicateException` | 동작 엔드포인트(좋아요)는 멱등이라 409 를 쓰지 않는다 |
| 422 | 요청 body·쿼리 형식 검증 실패 | (`RequestValidationError`) | `fields` 에 필드별 메시지 |
| 500 | 처리 못 한 서버 오류 | (글로벌 핸들러) | 표에 적지 않는다 — 모든 엔드포인트 공통 |

- 422 는 body·쿼리·경로 파라미터가 있는 엔드포인트에 항상 적는다.
- 확인 순서: 401(인증) → 404(리소스 존재) → 403(권한) → 400/409(업무 규칙).

### 422 응답 모양 (`app/common/handlers.py` 기준)

최상위 `message` 는 고정 문구, 필드별 메시지는 `fields` 에 담긴다. `fields` 의 키 규칙:

| 위치 | 키 | 예 |
|---|---|---|
| body 필드 | 필드명 그대로 | `title` |
| body 중첩·배열 | 점으로 연결 | `tags.0`, `author.username` |
| 쿼리 파라미터 | `query.` + kebab-case 이름 | `query.page-size` |
| 경로 파라미터 | `path.` + 이름 | `path.post_id` |

```json
{ "status": "fail",
  "data": { "code": 422, "message": "입력값이 올바르지 않습니다.",
            "fields": { "title": ["..."], "query.page-size": ["..."] } } }
```

> 필드별 메시지(`"..."`)는 현재 Pydantic 기본 **영어** 문구다. 화면에 그대로 보여주지 말고, 프론트는 최상위 `message` 나 자체 문구를 쓴다.

## 4. 엔드포인트 명세 템플릿

`frontend/swagger/docs.md` 의 엔드포인트 블록과 같은 형식이다. Response 예시는 envelope 의 **`data` 안쪽만** 적는다(envelope 골격은 공통 규칙).

````markdown
### POST /api/posts

- **설명**: 포스트 작성 — 슬러그는 제목으로 자동 발급
- **인증**: 없음 | 로그인 필요 | 로그인 필요(staff 전용) | 로그인 필요(작성자 또는 staff)
- **응답 형태**: 단건 (201)   ← 단건 | 목록(페이지) | 목록(커서) | null
- **파라미터**: 없음   ← 있으면 아래 목록 예시처럼 표로

- **Request Body** (`PostCreateRequest`):

| 필드 | 타입 | 필수 | nullable | 제약 |
|---|---|---|---|---|
| title | string | ✅ | ❌ | 1~255자 |
| is_published | bool | ❌ | ❌ | 기본 false |

- **Response `data`** (`PostResponse`):

```json
{ "id": 1, "title": "첫 글", "is_published": false, "created_at": "2026-01-01T09:30:00.123456" }
```

| 필드 | 타입 | nullable | 설명 |
|---|---|---|---|
| id | int | ❌ | |

- **에러**:

| code | 조건 | message |
|---|---|---|
| 409 | 같은 슬러그 존재 | 이미 존재하는 슬러그입니다. |
| 422 | body 검증 실패 | 입력값이 올바르지 않습니다. (fields: `title` 등) |
````

목록 엔드포인트는 Response 를 이렇게 적는다:

````markdown
- **응답 형태**: 목록(페이지) — `results` 아이템: `PostSummaryResponse`
- **파라미터**:

| 이름 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| page | query | int | ❌ | 1 | 페이지 번호 (1부터) |
| page-size | query | int | ❌ | 20 | 페이지 크기 (최대 100) |
| sort | query | string | ❌ | latest | 정렬 — `latest`(최신순), `popular`(좋아요순) |
````

---

## 체크리스트

- [ ] 엔드포인트마다 응답 형태(단건/목록(페이지)/목록(커서)/null)와 status 가 "1. 응답 형태 선택" 표대로?
- [ ] 생성 201, 삭제 200 + null, 204 없음?
- [ ] 동작 엔드포인트가 POST(켜기)/DELETE(끄기) 쌍 + 멱등(409 없음)? (누적 카운터 예외는 "멱등 아님" 명시)
- [ ] 경로 복수형 kebab-case, 경로 파라미터 snake_case, 쿼리 kebab-case?
- [ ] 정렬 `sort` 허용값·기본값이 표에 적혀 있음?
- [ ] body 필드 snake_case, Boolean `is_`/`has_`, 날짜 예시에 `Z` 없음?
- [ ] PATCH body 의 nullable 이 모델 컬럼과 일치 (NOT NULL 필드에 null 불가)?
- [ ] 에러 표의 message 가 한국어 문장 + `exceptions.py` 와 동일?
- [ ] body·쿼리·경로 파라미터가 있는 엔드포인트에 422 행 있음?
- [ ] Response 예시가 `data` 안쪽만, envelope 형식 임의 변형 없음?

## 금지 사항

- ❌ envelope 를 이 문서나 spec 에서 다시 정의·변형 (원본은 `exception-handling.md`)
- ❌ 204 응답, `{"detail": ...}` 형식, envelope 없는 응답 설계
- ❌ 피드가 아닌 목록에 커서형 사용 (또는 반대)
- ❌ 범위 밖 페이지에 404, 동작 엔드포인트 중복 호출에 409
- ❌ 422 필드별 영어 메시지를 화면 문구로 전제한 설계
- ❌ 명세의 에러 message 와 예외 클래스 message 불일치
- ❌ 코드·요구사항에 근거 없는 필드 추측 — 모르면 `TODO(확인 필요)`
