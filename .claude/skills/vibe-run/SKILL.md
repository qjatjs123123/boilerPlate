---
name: vibe-run
description: 앱을 실행해 화면으로 확인하게 한다 — 사용자가 "보여줘", "실행해줘", "켜줘", "어떻게 확인해", "화면 보고 싶어"라고 할 때 사용.
---

# vibe-run — 앱 실행과 확인 안내

1. 개발 환경이 준비 안 됐으면 vibe-setup 스킬을 먼저 따른다.
2. `make db`로 DB를 켠다.
3. 서버를 **백그라운드**로 실행한다: `make dev-backend`, `make dev-frontend` (각각 run_in_background).
4. `curl -s http://localhost:8000/api/health`가 `"status":"success"`를 돌려줄 때까지 기다린다(최대 60초).
5. 사용자에게 안내한다:
   - 화면: http://localhost:3000
   - 방금 만든 기능이 있으면 그 페이지 주소(예: http://localhost:3000/{경로})
   - API 문서(궁금한 경우): http://localhost:8000/docs
6. 포트가 이미 사용 중이면 이미 실행 중인지 먼저 확인하고(같은 앱이면 그대로 안내), 다른 프로그램이면 사용자에게 알린다.
