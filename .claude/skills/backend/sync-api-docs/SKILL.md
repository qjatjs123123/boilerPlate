---
name: backend-sync-api-docs
description: 실제 백엔드 코드(app.openapi())로부터 frontend/swagger/docs.md API 계약 문서를 생성·갱신하는 절차.
---

# backend/sync-api-docs — 백엔드 구현 코드 → `frontend/swagger/docs.md` API 계약 문서 생성

> 절차 스킬 — 슬래시 커맨드가 아니다. 표기법·vibe-build 모드·커밋 절차·spec 번호 규칙은 **`.claude/skills/COMMON.md` 를 먼저 읽고** 따른다.

> **vibe-build 모드** — 공통 규칙은 `COMMON.md` §2 (메인에서는 커밋 없음 · 워크트리는 Task별 커밋 · 중간 확인 없음). 이 스킬만의 차이: openapi 추출 오류를 고치느라 백엔드를 수정한 경우도 별도 커밋하지 않는다.

**입력**: 도메인 이름 (넘겨받은 입력, 소문자 단수형 — 예: `post`, `user`. 공백 구분으로 여러 개 지정 가능. **생략 시 전 도메인**)
**목적**: 백엔드에 **실제로 구현된 코드**를 단일 진실로 삼아, `frontend/spec-create`·`frontend/spec-run`이 읽는 API 계약 문서 `frontend/swagger/docs.md`를 생성·갱신한다. 기억·추측으로 스키마를 쓰지 않는다 — 근거는 ① FastAPI `app.openapi()` 스펙 ② 도메인 코드(router/schemas/service/exceptions) 두 가지뿐이다.

**정렬 기준**: 응답 envelope 스펙의 단일 출처는 `.claude/rules/backend/exception-handling.md`. 이 문서의 소비자는 `frontend/spec-create`·`frontend/spec-run`과 `.claude/rules/frontend/models-layer.md`(Zod DTO 스키마)·`types-layer.md`.

> 예시: `backend/sync-api-docs post` → `frontend/swagger/docs.md`의 `## post` 섹션 생성/교체

---

## 사전 조건

- 모노레포 루트에 `backend/app/main.py` 존재 (FastAPI 앱)
- 백엔드 Python 실행 수단 확보 — 우선순위: `backend/.venv/bin/python` → `uv run python` → 실패 시 사용자에게 알리고 중단
- `app.openapi()`는 DB 연결 없이 동작해야 한다 — import 에러가 나면 **백엔드 코드 문제이므로 문서 생성 전에 먼저 수정**

하나라도 불만족 시 추측으로 진행하지 말고 중단한다.

---

## 실행 절차

### 1️⃣ OpenAPI 스펙 추출 (단일 진실)

```bash
cd backend && .venv/bin/python -c \
  "from app.main import app; import json; print(json.dumps(app.openapi(), ensure_ascii=False))" \
  > ../.harness/openapi-spec.json
```

- `frontend/public/openapi.json` 등 **어떤 파일도 이 스킬이 생성·수정하지 않는다** — 산출물은 오직 `frontend/swagger/docs.md`.
- 스펙에서 수집: `paths`(메서드·경로·operation_id·파라미터·requestBody·responses), `components.schemas`(Pydantic 스키마 필드·타입·필수 여부·제약).
- 대상 도메인 결정: 넘겨받은 입력가 있으면 해당 도메인만, 없으면 `backend/app/domains/*/router.py`가 존재하는 전 도메인. 경로 prefix(`/api/{복수형}`)로 도메인 ↔ paths를 매핑한다.

### 2️⃣ 코드 보강 수집 (OpenAPI가 못 담는 정보)

대상 도메인마다 다음 파일을 **실제로 읽는다**:

| 파일 | 수집 항목 |
|---|---|
| `domains/{domain}/router.py` | 인증 의존성(`get_current_user`/`_optional`/없음), 쿼리 파라미터 **kebab-case alias**, prefix, status_code |
| `domains/{domain}/service.py` | 권한 시맨틱 — staff 전용, 작성자 본인 확인 등 (도메인 예외 raise 분기) |
| `domains/{domain}/exceptions.py` | 도메인 예외별 `status_code` + 한국어 `message` → 에러 표의 근거 |
| `domains/{domain}/schemas.py` | `Field` 제약(min/max/ge/le), Optional/nullable, 기본값 |

- 스펙·코드 어디에서도 확인 불가한 항목은 추측하지 말고 `TODO(확인 필요)`로 표기한다.

### 3️⃣ `frontend/swagger/docs.md` 생성/갱신

- **파일이 없으면**: 아래 골격으로 신규 생성 (공통 섹션 + 대상 도메인 섹션).
- **파일이 있으면**: 대상 도메인의 `## {domain}` 섹션만 통째로 교체 — **다른 도메인 섹션과 공통 섹션은 보존**.
- 문서 최상단에 자동 생성 경고를 유지한다.

**문서 골격 (고정 템플릿)**:

````markdown
<!-- ⚠️ 자동 생성 문서 — 직접 수정 금지. 갱신: backend/sync-api-docs {domain} -->
# API 계약 문서 (swagger/docs.md)

## 공통

- **Base URL**: `http://localhost:8000` (개발 기준)
- **인증**: `backend/app/core/security.py` 기준 (현재 `X-User-Id: {사용자 ID}` 헤더 스텁 — JWT 로 교체 예정). 엔드포인트별 "인증" 항목 참조
- **필드 네이밍**: 응답·요청 body는 **snake_case** (camelCase 변환은 프론트 Mapper 책임)
- **쿼리 파라미터**: **kebab-case** (`page-size`, `search-keyword`)
- **날짜**: UTC 기준, 타임존 표기 없는 ISO8601 (`"2026-01-01T09:30:00.123456"`)
- **응답 envelope** (원본 스펙: `.claude/rules/backend/exception-handling.md`):
  - 성공: `{ "status": "success", "data": ... }`
  - 목록(표준): `data = { "results": [...], "pagination": { "current_page", "num_pages", "page_size", "total_count", "has_previous", "has_next" } }`
  - 목록(커서, 피드 전용): `data = { "results": [...], "pagination": { "next_cursor", "has_next" } }`
  - 4xx: `{ "status": "fail", "data": { "code", "message", "fields" } }`
  - 5xx: `{ "status": "error", "data": { "code", "message" } }`

## {domain}

### {METHOD} {path}

- **설명**: {한 줄 설명 — router docstring 기반}
- **인증**: 없음 | 로그인 필요 | 로그인 필요(staff 전용) | 로그인 필요(작성자 또는 staff)
- **응답 형태**: 단건 ({status}) | 목록(페이지) | 목록(커서) | null — 기준은 `.claude/skills/backend/api-spec/SKILL.md`
- **파라미터**:

| 이름 | 위치 | 타입 | 필수 | 기본값 | 설명 |
|---|---|---|---|---|---|
| page | query | int | ❌ | 1 | 페이지 번호 |

- **Request Body** (`{스키마명}`): — 없으면 생략

| 필드 | 타입 | 필수 | nullable | 제약 |
|---|---|---|---|---|
| title | string | ✅ | ❌ | 1~255자 |

- **Response `data`** (`{스키마명}`):

```json
{ "id": 1, "title": "...", "created_at": "2026-01-01T09:30:00.123456" }
```

| 필드 | 타입 | nullable | 설명 |
|---|---|---|---|
| id | int | ❌ | |

- **에러**:

| code | 조건 | message |
|---|---|---|
| 403 | staff 아님 | 공지사항에 대한 권한이 없습니다. |
| 404 | 존재하지 않는 ID | 공지사항을 찾을 수 없습니다. |
| 422 | body 검증 실패 | (fields에 필드별 메시지) |
````

- 공통 섹션의 envelope·날짜 형식은 생성할 때마다 원본(`exception-handling.md` 「응답 envelope 스펙」, `api-spec` 스킬 「URL·파라미터 규칙」)을 읽고 맞춘다 — 위 골격의 문구는 현재 원본을 옮긴 것이며, 원본과 다르면 원본을 따른다.
- Response 예시 JSON은 envelope의 **`data` 내부만** 기록한다 (envelope 골격은 공통 섹션이 담당).
- 목록 엔드포인트는 `results` 아이템 스키마와 pagination 형(표준/커서)을 명시한다.

### 4️⃣ 검증

- OpenAPI `paths`의 대상 도메인 엔드포인트 수 == 문서의 `### ` 엔드포인트 수 — 불일치 시 누락을 찾아 보정.
- `exceptions.py`의 모든 도메인 예외가 최소 1개 엔드포인트의 에러 표에 등장하는지 확인.
- `TODO(확인 필요)` 표기가 남아 있으면 최종 리포트에 목록으로 노출.

### 5️⃣ 리포트

`git diff frontend/swagger/docs.md` 기반으로 요약:

```
✅ backend/sync-api-docs 완료 — frontend/swagger/docs.md
갱신 도메인: post (7 엔드포인트)
  + POST /api/posts/bulk-delete (신규)
  ~ PATCH /api/posts/{post_id} (request body 변경: category 추가)
⚠️ TODO(확인 필요): 없음
```

---

## 완료 조건

- [ ] 대상 도메인의 모든 엔드포인트가 문서화됨 (OpenAPI paths 수와 일치)
- [ ] 엔드포인트마다 인증·파라미터·request/response 스키마·에러 표 존재
- [ ] nullable/optional·제약·날짜 형식이 코드와 일치 (추측 0건)
- [ ] 다른 도메인 섹션·공통 섹션이 훼손되지 않음

## 완료 커밋

완료 조건을 모두 충족하면 `git add frontend/swagger/docs.md` (명시적 경로, `git add -A` 금지) 후
`docs: swagger/docs.md {domain} 섹션 갱신 (sync-api-docs)` 메시지로 커밋한다 (전 도메인이면 `{domain}` 대신 `전 도메인`). push 금지.
`app.openapi()` import 에러를 고치느라 백엔드 코드를 수정했다면 그 파일은 `fix: openapi 추출 오류 수정 (sync-api-docs)` 로 **별도 커밋**한다 — 문서와 코드 수정을 한 커밋에 섞지 않는다.

## 금지 사항

- ❌ `frontend/public/openapi.json` 생성·수정 (범위 외 — 필요 시 `backend/scripts/export_openapi.py` 직접 실행)
- ❌ 스펙·코드에 없는 필드를 추측으로 기재 (불명 항목은 `TODO(확인 필요)`)
- ❌ 사용자에게 docs.md 수동 편집 요구 (자동 생성 문서 — 수정은 백엔드 코드에서)
- ❌ 서버 기동(`uvicorn`) — 스펙 추출은 import만으로 수행
