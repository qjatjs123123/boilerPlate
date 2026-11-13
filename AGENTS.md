# Agent Orientation Map

> Next.js 16 + FastAPI 모노레포 템플릿. 비개발자 바이브코딩용 하네스 내장. 처음 들어오면 이 파일부터 읽는다.

## Stack

| 영역 | 기술 |
|---|---|
| Frontend | Next.js 16 App Router, React 19, TypeScript, Tailwind 4, TanStack Query 5, Zod, axios |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic 2 |
| DB | PostgreSQL 16 (docker compose) |
| Test | pytest / Vitest + MSW / Playwright |
| Tooling | pnpm, uv, ruff, ESLint, Make |

## Architecture Layers

의존은 **한 방향**으로만. 역방향·건너뛰기 import 는 기계적으로 차단된다.

```
backend  : router → service → repository → models      (schemas 는 router/service 경계 DTO)
frontend : app(라우팅) → features/{도메인}/{pages → components → hooks → store → queries → services → models → types}   (axios 는 lib/axios 를 거쳐 services 만)
```
상세와 위반 수정 방법: `docs/architecture/LAYERS.md`

**프론트엔드 작업 전 필독**: `.claude/rules/frontend/architecture.md` — 폴더별 역할(app·components·features·lib), 계층 import 허용표, utils/store 위치, 강제 방식의 단일 출처.

## Directory

```
.
├── CLAUDE.md / AGENTS.md / ARCHITECTURE.md
├── Makefile                      setup · dev · check · e2e · gc · worktree-setup
├── .claude/
│   ├── settings.json             권한(allow/deny) + 훅 등록
│   ├── hooks/                    SessionStart · UserPromptSubmit · PostToolUse · Stop(품질 게이트)
│   ├── rules/{backend,frontend}/ 레이어별 코딩 규칙 (paths 매칭 시 자동 로드)
│   ├── skills/                   vibe-setup · vibe-build(+harness.md 최종 검증 루프) · vibe-run · vibe-refactor (진입점, 자동 호출)
│   │   ├── frontend/             zod-usage · error-toast · frontend-design · spec-create · spec-run · refactor · browser-check
│   │   └── backend/              api-spec · db-design · schema-cleanup · spec-create · spec-run · refactor · verify · sync-api-docs
│   ├── agents/                   db-design-reviewer · spec-reviewer · backend-dev · frontend-dev (서버·화면 개발은 묶음별 워크트리에서 병렬)
│   └── templates/spec-template.md
├── backend/
│   ├── app/{common,core,db}/     횡단 관심사 (envelope, 예외, 설정, DB)
│   ├── app/domains/{domain}/     router · service · repository · schemas · models · exceptions
│   ├── alembic/                  마이그레이션
│   └── tests/{unit,api,architecture}/
├── frontend/
│   ├── src/
│   │   ├── app/                  Page — 라우팅만 (features/*/pages 를 export, layout.tsx 가 AppShell)
│   │   ├── features/{domain}/    Feature — pages · components · models · services · queries · hooks · store · constants · types
│   │   └── components/ lib/ utils/  Shared — 공용 UI(ui·layout·shared) / axios·ReactQueryProvider / errors·formatDate
│   ├── e2e/                      Playwright (fixtures.ts 사용)
│   └── swagger/docs.md           API 계약 (sync-api-docs 가 생성)
├── spec/                         개발 요청별 spec 문서 — README.md(색인) · backend/ · frontend/ (같은 요청 = 같은 번호)
├── docs/
│   ├── CONVENTIONS.md · TROUBLESHOOTING.md   공통 (사내 컨벤션·자주 나는 에러)
│   ├── frontend/ · backend/      영역별 TROUBLESHOOTING (backend 는 ARCHITECTURE·CONVENTIONS·DOMAIN-MAP(데이터 개념 지도)·ERD(자동 생성) 도) — 프론트 구조·규칙은 .claude/rules/frontend/
│   └── architecture/LAYERS.md    계층 지도 + 강제 방식
├── scripts/                      doctor.sh, gc/
└── .harness/                     run 상태·로그 (git 무시)
```

## Commands

```sh
make setup     # 최초 1회
make dev       # 백엔드 :8000 + 프론트 :3000
make check     # ruff + pytest + eslint + tsc + vitest + build
make e2e       # Playwright (SPEC=e2e/x.spec.ts 로 한 파일만, HARNESS_RUN_DIR=... 로 콘솔 에러 기록)
make gc        # 엔트로피 점검 (보고 전용)
```

## Where to Look First

| 작업 | 시작점 |
|---|---|
| 새 기능 전체 흐름 | `.claude/skills/vibe-build/SKILL.md` |
| 백엔드 계층 규칙·템플릿 | `.claude/rules/backend/*.md` |
| 프론트 전체 구조 | `.claude/rules/frontend/architecture.md` |
| 프론트 계층 규칙·템플릿 | `.claude/rules/frontend/*.md` |
| 응답 envelope 스펙 | `.claude/rules/backend/exception-handling.md` |
| API 계약 | `frontend/swagger/docs.md` |
| 계층 위반 에러 | 에러 메시지에 적힌 `.claude/rules/...` 파일 |
| 구조·요청 흐름 | 루트 `ARCHITECTURE.md` → 프론트 `.claude/rules/frontend/architecture.md` · 백엔드 `docs/backend/ARCHITECTURE.md` |
| 린터가 못 잡는 규칙 | `docs/CONVENTIONS.md` → 프론트 `.claude/rules/frontend/` · 백엔드 `docs/backend/CONVENTIONS.md` |
| 자주 나는 에러 | `docs/TROUBLESHOOTING.md` → `docs/{frontend,backend}/TROUBLESHOOTING.md` |
| 만든 기능 / 진행 중 작업 | `spec/README.md` (요청별 spec 색인) |

## Constraints

- MUST: 코드 변경 후 `make check` 통과 (Stop 훅은 바뀐 쪽의 lint·타입·테스트·e2e 만 강제 — 빌드는 `make check`·CI 가 확인)
- MUST: 새 백엔드 도메인 → `alembic/env.py` import + `main.py` 라우터 등록
- MUST NOT: `HTTPException`, service→service 호출, 컴포넌트에서 axios 직접 사용 (경계 테스트/ESLint 가 차단)
- MUST NOT: `.env*` 읽기, `git push`, 테스트 약화, `known-violations.json` 항목 추가
- PREFER: `.claude/rules/**` 계층 규칙의 템플릿 구조·스타일을 따름
