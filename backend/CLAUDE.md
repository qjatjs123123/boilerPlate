# CLAUDE.md — Backend

FastAPI + SQLAlchemy + PostgreSQL 기반 서버 레이어. **스프링식 레이어드 아키텍처** (Controller → Service → Repository → Model).

## 아키텍처 — 도메인 단위 4계층

```
app/
├── domains/{domain}/        # 도메인 단위 응집 (예: user, post)
│   ├── router.py            # Controller — HTTP 입출력만 (thin)
│   ├── service.py           # 비즈니스 로직 + 트랜잭션 경계
│   ├── repository.py        # DB 접근 전담 (SQLAlchemy 2.0 select)
│   ├── schemas.py           # Pydantic Request/Response DTO
│   ├── models.py            # SQLAlchemy 엔티티
│   └── exceptions.py        # 도메인 예외 (AppException 상속)
├── core/                    # config, security (get_current_user — 현재 X-User-Id 개발용 스텁)
├── common/                  # 횡단 관심사
│   ├── exceptions.py        #   AppException 베이스
│   ├── handlers.py          #   글로벌 예외 핸들러 (envelope 강제)
│   ├── response.py          #   SuccessResponse / success_response
│   ├── pagination.py        #   PageParams / paginate / cursor_page
│   └── logging.py           #   log_event 구조화 로깅
├── db/                      # base.py (engine/Base), deps.py (get_db)
└── main.py                  # 앱 조립 (라우터 등록, 핸들러 등록, CORS)
```

**의존 방향**: `router → service → repository → models` (경계 테스트가 강제하는 것: 도메인 간 import·common→domain·models 의 프레임워크 import — 나머지 방향은 규칙·리뷰로 지킨다, `docs/architecture/LAYERS.md`)

| 규칙 | 설명 |
|---|---|
| 역방향 금지 | service가 router를, models가 repository를 모름 |
| 건너뛰기 금지 | router 엔드포인트가 repository/DB 를 직접 호출 금지 (deps 함수에서 repository 를 만들어 service 에 주입하는 것은 허용 — `router-layer.md`) |
| 예외 흐름 | service가 도메인 예외 raise → `common/handlers.py`가 envelope 변환. `HTTPException` 금지 |
| 트랜잭션 | repository는 `flush()`까지, `commit()`은 service |
| 도메인 간 | 다른 도메인의 repository를 주입해 사용. service → service 호출 금지 |

레이어별 상세 규칙·템플릿·테스트 규약은 `.claude/rules/backend/*.md` 참조 (router-layer, service-layer, repository-layer, schema-layer, model-layer, exception-handling, test-convention, python-convention).

## 개발 플로우

사용자 요청은 `vibe-build` 스킬이 아래 절차 스킬(`.claude/skills/backend/<이름>/SKILL.md`)을 순서대로 읽고 따른다 (사용자가 직접 입력할 필요 없음).

```
backend/spec-create <요구사항>  → spec/backend/{NNN}-*.md (models → repository → service → router → 통합 테스트)
backend/spec-run {NNN}          → Task 순차 구현 (pytest 게이트, 끝나면 backend/refactor)
backend/verify                  → 서버 기동 + curl 로 envelope 실검증
```

새 도메인을 만들면 반드시:
0. 테이블 설계를 `data-model.yaml` 에 먼저 반영 (db-design 스킬 + reviewer PASS)
1. `alembic/env.py` 에 `import app.domains.{domain}.models` 추가 → `alembic revision --autogenerate` → 파일 검토 → `alembic upgrade head`
2. `app/main.py` 에 `app.include_router(...)` 등록
3. 구조·스타일은 `.claude/rules/backend/*.md` 의 계층 규칙과 템플릿을 따른다

## 기술 스택

| 항목 | 기술 |
|---|---|
| Runtime | Python 3.11+ (uv 로 가상환경 관리) |
| Framework | FastAPI |
| ORM / Migration | SQLAlchemy 2.0 / Alembic |
| Database | PostgreSQL 16 (docker compose) |
| Validation | Pydantic v2 |
| Lint / Format | ruff |
| Testing | pytest + httpx TestClient |

## 기계적 강제 (하네스)

- `tests/architecture/test_boundary.py` — 계층 금지 규칙을 AST로 검사. 위반 메시지에 읽을 rules 파일이 적혀 있다.
  - 기존 위반은 `tests/architecture/known-violations.json` 에만 기록되며 **줄어들 수만 있다** (새 항목 추가 금지).
- `tests/architecture/test_schema.py` — DB 설계 단일 출처 `data-model.yaml` 과 모델(`Base.metadata`)의 1:1 일치 + 정규화 규칙(목록 컬럼·JSON·반복 컬럼·값 복사·사유 없는 집계 컬럼 등) 검사. 규칙: `.claude/rules/backend/db-design.md`.
- 테이블 추가·변경은 `.claude/skills/backend/db-design/SKILL.md` 절차 → spec 데이터 모델 블록 → `db-design-reviewer` PASS → `data-model.yaml` → models.py 순서.
- 작업 종료 시 Stop 훅이 `ruff` + `pytest` + `alembic check` 를 다시 돌린다. 실패하면 종료가 막힌다.

## 인증 (현재: 개발용 스텁)

- `app/core/security.py` 의 `get_current_user` 는 `X-User-Id` 헤더로 사용자를 찾는다. **실서비스 전 JWT 등으로 교체 필요.**
- 개발용 관리자: `scripts/seed_dev_user.py` 가 `dev-admin`(is_staff) 을 만든다. 프론트 `NEXT_PUBLIC_DEV_USER_ID` 와 id 가 같아야 한다.
- 개발용 일반 사용자: 같은 스크립트가 `dev-user`(staff 아님)도 만들고 id 를 출력한다. "남의 리소스는 수정·삭제 불가(403)" 같은 권한 검증에 `X-User-Id: {dev-user id}` 로 쓴다 — DB 에 사용자를 직접 넣지 않는다.
- 인증은 라우터의 `Depends(get_current_user)`, **권한 판정은 service 에서 도메인 예외로** (`HTTPException` 금지).

## 페이지네이션

- 표준: 페이지 번호 (`page`, `page-size` 쿼리 파라미터 — kebab-case alias) → `paginate()`
- 피드(최신/트렌딩)성 목록만 커서 변형 → `cursor_page()`
- 두 방식 모두 `data.results + data.pagination` 골격 동일

## 도메인 구성

```
app/domains/
├── user/      # 사용자 (models, repository) — 인증 스텁이 사용
└── post/      # 게시판 — 글 목록·상세·작성·수정·삭제·검색·조회수·이전/다음 글 (spec 001~003)
```

## 개발 명령어 (루트 Makefile)

```bash
make setup          # 최초 1회 (venv, DB, 마이그레이션, 개발 사용자)
make db             # DB 컨테이너 기동
make db-port PORT=5433  # 5432 충돌 시 backend/.env 의 DB 포트 변경 (내용 출력 없음)
make dev-backend    # http://localhost:8000 (API 문서: /docs)
make check-backend  # ruff + pytest (경계·스키마 테스트 포함) + alembic check

# backend/ 안에서
.venv/bin/alembic revision --autogenerate -m "add_xxx"
.venv/bin/alembic upgrade head
.venv/bin/pytest tests/unit/domains/{domain}
.venv/bin/python scripts/export_openapi.py   # frontend/public/openapi.json 갱신
```

## 환경 변수 (`backend/.env` — `.env.example` 에서 복사, 내용 읽기 금지)

`.env.example` 참고: `COMPOSE_PROJECT_NAME`, `POSTGRES_*`, `DATABASE_URL`, `JWT_SECRET`, `FRONTEND_URL`, `BACKEND_URL`, `DEBUG`

## 응답 Envelope (프론트엔드 계약 — 단일 출처: `.claude/rules/backend/exception-handling.md`)

모든 API 응답은 아래 3형식 중 하나. 글로벌 예외 핸들러(`app/common/handlers.py`)가 강제한다.

```jsonc
// 성공 (2xx)
{ "status": "success", "data": { ... } }

// 목록 성공 — 표준 (페이지 번호 기반)
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

// 클라이언트 오류 (4xx)
{ "status": "fail",
  "data": { "code": 404, "message": "게시글을 찾을 수 없습니다.", "fields": { } } }

// 서버 오류 (5xx)
{ "status": "error", "data": { "code": 500, "message": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요." } }
```

- 쿼리 파라미터는 **kebab-case**: `page`, `page-size`, `search-keyword`.
- 필드명은 snake_case — camelCase 변환은 프론트 Mapper 책임.

