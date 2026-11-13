# 자주 나는 문제와 해결법 — 백엔드

공통 문제(환경 준비, Docker, 포트, 품질 게이트)는 [../TROUBLESHOOTING.md](../TROUBLESHOOTING.md).

## 경계 테스트 실패 (`tests/architecture/test_boundary.py`)
- 증상: `no-http-exception`, `service-no-query`, `router-no-db` 같은 규칙 ID 와 함께 실패
- 해결: 메시지에 적힌 `.claude/rules/backend/*.md` 를 읽고 코드를 올바른 계층으로 옮긴다 (예: service 의 `select` → repository 메서드로). `known-violations.json` 에 항목을 **추가하지 않는다** (줄이기만 가능).

## 테스트가 DB 연결 에러로 실패
- 증상: `connection refused`, `could not connect to server` (repository 테스트·api 테스트)
- 원인: repository 테스트는 실제 PostgreSQL 을 쓴다 (`conftest.py` 의 `db_session`, 테스트별 rollback)
- 해결: `make db` 로 DB 를 켜고 다시 실행. 테이블이 없다는 에러면 아래 「마이그레이션」.

## 마이그레이션 에러
- `Target database is not up to date` → `cd backend && .venv/bin/alembic upgrade head`
- autogenerate 가 빈 마이그레이션을 만듦 → 새 도메인 models 를 `alembic/env.py` 에 import 했는지 확인
- autogenerate 가 rename 을 drop + add 로 만듦 → 데이터가 사라지므로 `op.alter_column` 등으로 직접 고친다
- `Can't locate revision` / 꼬임 → 개발 데이터라면 사용자에게 **DB 데이터가 모두 지워진다**고 설명하고 확인받은 뒤 `cd backend && docker compose down -v && make db && .venv/bin/alembic upgrade head && .venv/bin/python scripts/seed_dev_user.py`

## 401 인증 ("인증이 필요합니다.")
- 원인: `X-User-Id` 헤더 없음 / 숫자 아님 / users 테이블에 해당 id 없음 (개발용 인증 스텁)
- 해결: 프론트는 `NEXT_PUBLIC_DEV_USER_ID` 로 헤더를 붙인다. DB 를 초기화했다면 `cd backend && .venv/bin/python scripts/seed_dev_user.py` 로 개발용 사용자를 다시 만든다. curl 로 확인할 때는 `-H "X-User-Id: 1"`.

## 403 권한 ("본인이 작성한 게시글만 수정·삭제할 수 있습니다.")
- 원인: 게시글 수정·삭제는 작성자 본인만 (`app/domains/post/exceptions.py` 의 403 메시지). staff 전용 기능이 생기면 `users.is_staff` 로 판정한다.
- 해결: 의도된 동작인지 먼저 확인. 요청 헤더 `X-User-Id` 가 글 작성자인지, 개발용 사용자(`dev-admin`/`dev-user`)를 seed 스크립트 출력으로 확인한다.

## CORS 에러 (브라우저 콘솔)
- 원인: 프론트 주소가 백엔드 `settings.frontend_url`(기본 `http://localhost:3000`)과 다름 (포트를 바꾼 경우 등)
- 해결: 사용자에게 `backend/.env` 의 `FRONTEND_URL` 을 실제 프론트 주소로 바꿔 달라고 정확한 줄을 알려준다 (`.env` 는 Claude 가 수정 불가).

## 응답이 `{"detail": ...}` 형식으로 나옴
- 원인: `HTTPException` 을 직접 raise 했거나 `register_exception_handlers` 가 빠짐
- 해결: 도메인 예외(`exceptions.py`)로 바꾸고, `app/main.py` 에서 핸들러 등록을 확인한다. 응답은 항상 envelope 여야 한다.

## 패키지를 추가했는데 import 에러
- `cd backend && uv pip install -e ".[dev]"` 로 다시 설치 (의존성은 `pyproject.toml` 에 추가).
