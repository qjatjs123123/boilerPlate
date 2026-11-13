# 자주 나는 문제와 해결법 — 공통

Claude 는 에러를 만나면 이 문서와 해당 영역 문서를 먼저 확인한다. 새로운 문제를 해결하면 알맞은 문서에 추가한다.
- 화면·브라우저·ESLint·Vitest·Playwright 문제 → [frontend/TROUBLESHOOTING.md](frontend/TROUBLESHOOTING.md)
- 서버·DB·마이그레이션·pytest 문제 → [backend/TROUBLESHOOTING.md](backend/TROUBLESHOOTING.md)

## 개발 환경이 준비되지 않음
- 증상: 세션 시작 상태에 "개발 환경: 준비 안 됨", `.venv` 나 `node_modules` 없음
- 해결: `vibe-setup` 스킬을 따른다 (`make setup` — env 파일 생성, DB 기동, 의존성 설치, 마이그레이션, 개발용 사용자 생성).

## Docker 가 실행되지 않음 (DB 만 Docker 사용)
- 증상: `Cannot connect to the Docker daemon`, `docker: command not found`, `make db` 실패
- 해결: 사용자에게 Docker Desktop 을 설치·실행해 달라고 쉬운 말로 안내한다. WSL 이면 Docker Desktop 설정의 WSL 연동이 켜져 있어야 한다. 실행되면 `make db`.

## 포트가 이미 사용 중
- 증상: `address already in use` (3000 프론트 / 8000 백엔드 / 5432 DB)
- 해결: 이전에 켠 개발 서버가 남아 있는지 먼저 확인(`lsof -i :8000`). 남은 프로세스면 종료, 다른 프로그램이면 사용자에게 포트를 바꿔도 되는지 묻는다. `.env` 는 Claude 가 직접 읽거나 고칠 수 없다 — DB 포트는 사용자 확인 후 `make db-port PORT=5433` 으로 바꾸고, 그 밖의 값은 사용자에게 바꿀 줄을 정확히 알려준다.

## 종료할 때 품질 게이트가 막음
- 증상: 작업을 끝내려는데 "품질 게이트 실패"로 종료가 차단됨 (최대 6회)
- 해결: 출력된 영역별 에러(백엔드 / 프론트)를 읽고 고친다. 규칙을 끄거나 테스트를 약화해서 통과시키지 않는다. 계층 위반 에러는 메시지에 적힌 `.claude/rules/...` 문서를 읽고 의존을 올바른 계층으로 옮긴다.

## 화면은 뜨는데 데이터가 안 나옴
1. 백엔드가 켜져 있는지: `curl -s http://localhost:8000/api/health` → `{"status":"success","data":{"status":"ok"}}`
2. 브라우저 콘솔의 에러 종류로 영역을 가른다:
   - CORS / Network Error → [backend/TROUBLESHOOTING.md](backend/TROUBLESHOOTING.md) 「CORS」
   - `DomainLayerError` (응답 형식 불일치) → [frontend/TROUBLESHOOTING.md](frontend/TROUBLESHOOTING.md) 「응답 형식 불일치」
   - 401 → [backend/TROUBLESHOOTING.md](backend/TROUBLESHOOTING.md) 「401 인증」
