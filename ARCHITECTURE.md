# Architecture

```
브라우저 ──▶ frontend (Next.js :3000) ──HTTP/JSON envelope──▶ backend (FastAPI :8000) ──▶ PostgreSQL
              src/app → src/features/{domain}/                  app/domains/{domain}/
              pages·components·hooks·queries·services·models    router·service·repository·models
```

- **계약**: 백엔드 응답은 항상 `{status, data}` envelope (`.claude/rules/backend/exception-handling.md`). 프론트는 `swagger/docs.md` 를 기준으로 Zod 스키마를 만든다.
- **도메인 단위 응집**: 기능 하나 = 백엔드 `app/domains/{x}/` + 프론트 `src/features/{x}/` 한 쌍 (프론트는 사내 3계층 Page `src/app/` · Feature `src/features/` · Shared).
- **횡단 관심사**: 백엔드 `app/common/` (예외·envelope·페이지네이션·로깅), 프론트 Shared 계층 `src/components/{ui,layout,shared}/`·`src/lib/`(axios)·`src/utils/`(에러) — 도메인을 import 하지 않는다.

- **실행 방식**: DB 만 Docker(`backend/docker-compose.yml`), 백엔드·프론트는 로컬 직접 실행(`make dev`). 브라우저가 `NEXT_PUBLIC_API_URL`(기본 `http://localhost:8000`)로 백엔드를 직접 호출하므로 백엔드에 CORS 설정(`settings.frontend_url`)이 있다.
- **인증**: 개발용 스텁 — 프론트가 `X-User-Id` 헤더를 붙이고 `app/core/security.py` 가 users 테이블에서 찾는다. 실서비스 전 JWT 로 교체 예정.
- **개발 순서**: backend spec-create(API 계약) → frontend spec-create → backend·frontend spec-run 을 묶음별로 병렬 → 합치기 → sync-api-docs → 계약 대조 → harness (비개발자 요청은 `vibe-build` 스킬이 자동 진행, 요청별 기록은 `spec/`).

계층 규칙·강제 방식·위반 수정법: [docs/architecture/LAYERS.md](docs/architecture/LAYERS.md) · 프론트 전체 지도: [.claude/rules/frontend/architecture.md](.claude/rules/frontend/architecture.md)

상세 문서: 프론트 [.claude/rules/frontend/architecture.md](.claude/rules/frontend/architecture.md) · [docs/backend/ARCHITECTURE.md](docs/backend/ARCHITECTURE.md)
