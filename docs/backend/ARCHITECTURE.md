# 백엔드 아키텍처 (backend/)

Python 3.11+ · FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic 2 · PostgreSQL 16 (Docker).
계층 규칙과 강제 방식의 단일 출처는 `.claude/rules/backend/*.md` + `../architecture/LAYERS.md` — 이 문서는 지도와 흐름만 담는다.

## 폴더 구조

| 폴더 | 역할 | 예시 |
|---|---|---|
| `app/domains/{기능}/` | 기능 모듈 (아래 계층) | `domains/user/`, `domains/{기능}/` |
| `app/common/` | 예외 베이스·글로벌 핸들러·envelope·페이지네이션·구조화 로깅. 도메인 import 금지 | `exceptions.py`, `handlers.py`, `response.py`, `pagination.py`, `logging.py` |
| `app/core/` | 환경 설정, 인증 의존성(현재 `X-User-Id` 스텁) | `config.py`, `security.py` |
| `app/db/` | 엔진·Base, 요청 단위 세션 `get_db` | `base.py`, `deps.py` |
| `app/main.py` | 앱 생성, CORS, `register_exception_handlers`, 도메인 라우터 등록 | |
| `alembic/` | 마이그레이션 (`env.py` 에 도메인 models import 등록) | |
| `scripts/` | `export_openapi.py`(openapi.json), `seed_dev_user.py`(개발용 사용자), `check_contract.py`(spec 계약 ↔ 실제 서버 대조), `check_envelope.py`(응답 envelope 검사), `gen_erd.py`(ERD 생성·최신 확인) | |
| `tests/` | `unit/`(service·repository·common), `api/`(엔드포인트), `architecture/`(경계 테스트 `test_boundary.py`·스키마 검사 `test_schema*.py`) | |

## 도메인 계층 — `app/domains/{기능}/`

```
router.py      HTTP 입출력 (thin) — 바인딩 → service → Response 스키마 → envelope   ─┐
service.py     유스케이스 + 존재·권한 검증 + 트랜잭션 경계(commit)                   │ 의존은
repository.py  DB 접근만 (select + scalars, flush 까지)                           │ 위 → 아래만
models.py      SQLAlchemy 엔티티 (컬럼·관계만)                                    ─┘
schemas.py     Pydantic DTO ({Entity}CreateRequest / UpdateRequest / Response)  — router·service 경계
exceptions.py  도메인 예외 (AppException 상속, status_code·message 클래스 속성)
```

## 요청 흐름 (공지사항 상세 조회 예시)

```
GET /api/{기능 복수형}/{id}
  └─ router.get_{기능}                 Depends(get_{기능}_service): get_db → {Domain}Repository → {Domain}Service
       └─ {Domain}Service.get_{기능}     없으면 raise {Domain}NotFoundException (404), commit(쓰기 시)
            └─ {Domain}Repository.find_by_id   select({Domain})... → {Domain} | None
       └─ success_response({Domain}Response.model_validate(entity))   → {"status":"success","data":{...}}

예외 발생 시 → app/common/handlers.py 가 envelope 로 변환
  AppException 4xx → {"status":"fail", ...} / 5xx·미처리 → {"status":"error", ...} + logger.exception
```

## 새 기능 하나가 거치는 파일

```
app/domains/{기능}/models.py          테이블
alembic/env.py                         모델 import 등록
alembic/versions/...                   마이그레이션 (autogenerate 후 검토)
app/domains/{기능}/schemas.py          요청·응답 DTO
app/domains/{기능}/exceptions.py       도메인 예외
app/domains/{기능}/repository.py       쿼리
app/domains/{기능}/service.py          유스케이스
app/domains/{기능}/router.py           URL + get_{기능}_service
app/main.py                            include_router 등록
tests/unit/domains/{기능}/test_repository.py   실제 DB (rollback 격리)
tests/unit/domains/{기능}/test_service.py      Mock(spec=Repository)
tests/api/test_{기능}.py                       dependency_overrides 로 service mock
→ 완료 후 sync-api-docs 로 frontend/swagger/docs.md 갱신
```

## 상세 규칙 위치

| 대상 | 파일 |
|---|---|
| router / service / repository / models / schemas | `.claude/rules/backend/{router,service,repository,model,schema}-layer.md` |
| 예외·응답 envelope (스펙 원본) | `.claude/rules/backend/exception-handling.md` |
| 테스트 / Python 함수 | `.claude/rules/backend/{test,python}-convention.md` |
| DI 체인 · 쿼리 패턴 (eager load·집계·원자적 카운터·커서) | `router-layer.md` · `repository-layer.md` |
