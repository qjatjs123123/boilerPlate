---
name: backend-verify
description: 백엔드 서버를 띄워 curl로 엔드포인트(status code·envelope)를 실검증하고 에러를 자동 수정하는 절차.
---

# backend/verify — 서버 기동 + curl 기반 엔드포인트 실시간 검증 & 자동 수정

> 절차 스킬 — 슬래시 커맨드가 아니다. 표기법·vibe-build 모드·커밋 절차·spec 번호 규칙은 **`.claude/skills/COMMON.md` 를 먼저 읽고** 따른다.

> **vibe-build 모드** — 공통 규칙은 `COMMON.md` §2 (메인에서는 커밋 없음 · 워크트리는 Task별 커밋 · 중간 확인 없음). 이 스킬만의 차이: 없음.

개발 중인 백엔드 엔드포인트를 **실제 서버를 띄워 curl로 검증**하고, 에러가 발견되면 **자동으로 수정**하는 루프.

## 입력 형태

```
backend/verify                              # /api/health + 등록된 전체 라우터 smoke
backend/verify --domain post                # post 도메인 엔드포인트만
backend/verify --endpoint "GET /api/posts"  # 특정 엔드포인트만
```

입력: 이 스킬을 따르라고 지시한 쪽이 넘겨준 내용 (위 형태 중 하나)

---

## 실행 절차

### 1️⃣ 선행 조건 확인

```bash
make db                                     # PostgreSQL 기동 (healthy 까지 대기)
cd backend && .venv/bin/alembic upgrade head # 마이그레이션 최신화
```

- DB가 안 뜨면 사용자에게 보고 후 중단 (docker 미설치·포트 충돌 등).

### 2️⃣ 서버 기동

- 먼저 `curl -s http://localhost:8000/api/health` 로 이미 떠 있는지 본다. `"status":"success"` 면 같은 앱이므로 그대로 사용, 다른 응답이면 다른 프로그램이므로 멈추고 보고한다.
- 꺼져 있으면 `make dev-backend` 를 **백그라운드**(run_in_background)로 실행하고, 위 curl 로 준비를 확인한다 (최대 10초). `--reload` 라 코드 수정이 자동 반영된다.

### 3️⃣ 라우터 등록 확인

```bash
curl -s http://localhost:8000/openapi.json -o .harness/openapi.json
backend/.venv/bin/python -c "import json; print(sorted(json.load(open('.harness/openapi.json'))['paths']))"
```

- 검증 대상 엔드포인트가 목록에 없으면 → `app/main.py`의 `include_router` 누락 여부 확인.

### 4️⃣ 엔드포인트 검증 루프

대상 엔드포인트마다 **성공 케이스 + 에러 케이스**를 `backend/scripts/check_envelope.py` 로 호출해 envelope 구조를 assert 한다 (jq 불필요 — 표준 라이브러리만 사용, 통과 exit 0 / 실패 exit 1 + 이유 출력). 레포 루트에서:

```bash
# 성공 — 목록(페이지) envelope
backend/.venv/bin/python backend/scripts/check_envelope.py GET /api/posts --expect success --code 200 --list page
# 에러 — 없는 리소스
backend/.venv/bin/python backend/scripts/check_envelope.py GET /api/posts/999999 --expect fail --code 404
# 검증 실패 — 422 + fields
backend/.venv/bin/python backend/scripts/check_envelope.py POST /api/posts --json '{}' --header X-User-Id:1 --expect fail --code 422
# 생성 — 201 (인증 스텁 헤더)
backend/.venv/bin/python backend/scripts/check_envelope.py POST /api/posts --json '{"title":"검증","content":"검증 본문"}' --header X-User-Id:1 --expect success --code 201
```

인증 필요 엔드포인트는 헤더 없이 401 fail envelope 확인 + `X-User-Id` 헤더로 성공 케이스까지가 기본. 실제 토큰 플로우는 통합 테스트 몫.
작성자·staff 전용 같은 **권한(403)** 은 개발용 일반 사용자 `dev-user`(`scripts/seed_dev_user.py` 가 만들고 id 를 출력 — 다시 실행해도 중복 없음)의 id 로 남의 리소스를 수정·삭제해 확인한다. DB 에 임시 사용자를 직접 넣지 않는다.
검증하려고 만든 데이터(글 등)는 끝나면 API 로 지운다 — 개발 DB 는 사용자가 보는 화면과 같은 DB 다.

### 5️⃣ 에러 분석 & 자동 수정 (최대 3회 루프)

**Case 1: 5xx / 미처리 예외**
```
서버 로그에서 traceback 확인 → 해당 파일·라인 분석 → 수정 → 서버 재시작(--reload면 자동) → 4️⃣ 재실행
```

**Case 2: envelope 형식 위반**
```
{"detail": ...} 반환 발견 → 글로벌 핸들러 미등록 또는 HTTPException 사용 흔적
→ exception-handling.md 기준으로 수정 → 재검증
```

**Case 3: 404 (라우트 자체 없음)**
```
openapi.json에 경로 없음 → include_router / prefix 오타 확인 → 수정 → 재검증
```

3회 초과 시 사용자에게 에러 상세 보고 후 중단.

### 6️⃣ 종료 및 보고

- 이 스킬이 띄운 서버 프로세스는 종료한다 (기존에 떠 있던 서버는 유지).
- **완료 커밋**: 전 엔드포인트 검증 통과 시점에 이 루프에서 **수정한 파일이 1개 이상이면** 그 파일들만 명시적 경로로 `git add`(`git add -A` 금지) 후 `fix: {요약} (backend/verify)` 메시지로 커밋한다. push 금지. 수정 0건이면 커밋 없음, 3회 초과 실패(❌ 잔존) 시 커밋하지 않고 보고만 한다.
- 보고 형식:

```
## 검증 결과
✅ GET /api/posts — success envelope + pagination OK
✅ GET /api/posts/{id} 404 — fail envelope OK
❌ POST /api/posts — 500 (수정 2회 시도, traceback: ...)
- 수정한 파일: app/domains/post/service.py
- 커밋: (실패 잔존으로 커밋 안 함)
```

---

## 금지 사항

- ❌ 검증 실패를 통과로 보고
- ❌ envelope assert 없이 status code만 확인
- ❌ 수정 루프에서 테스트 코드·assert를 약화시켜 통과
- ❌ 사용자가 띄워둔 기존 서버를 임의로 종료
