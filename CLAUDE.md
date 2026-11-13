# CLAUDE.md — 프로젝트 루트

Next.js(프론트) + FastAPI(백엔드) 모노레포. **비개발자가 말로 요청하면 하네스가 자동으로 설계·구현·검증하는** 템플릿이다.
구조 지도는 `AGENTS.md`, 계층 규칙은 `docs/architecture/LAYERS.md` → `.claude/rules/**`.
**프로젝트 `.claude/rules/**` 가 전역 `~/.claude/rules/**` 와 다르면 프로젝트 규칙이 우선**한다 (프론트는 사내 FE 컨벤션 반영: `src/` 3계층 Page·Feature·Shared 구조, 타입 `I`/`T` 접두사 — `.claude/rules/frontend/`).
문서는 `docs/` — 공통(CONVENTIONS·TROUBLESHOOTING) + `docs/frontend/`·`docs/backend/` 영역별. 구조 개요는 루트 `ARCHITECTURE.md`, 요청별 기록은 `spec/`. 에러를 만나면 TROUBLESHOOTING 부터 보고, 새로 해결한 에러는 해당 문서에 추가한다.

## 사용자 응대 원칙 (가장 중요)

- 사용자는 **비개발자**다. 코드·파일명·기술 용어 대신 **화면과 동작** 기준으로 설명한다.
- 사용자에게 슬래시 커맨드(`/...`)나 터미널 명령을 입력하라고 하지 않는다. 필요한 명령은 직접 실행한다.
- 코드 변경 요청은 **vibe-build 스킬**, 실행·확인 요청은 **vibe-run**, 환경 미준비 시 **vibe-setup** 을 따른다 (매 입력마다 훅이 상기시킨다).
- **확인을 받아야 하는 것**: 요구사항 확정, 데이터 삭제·DB 초기화, 기존 기능 동작 변경, 구조 대규모 변경, 외부 서비스 연동·비용 발생.
- 결과 보고는 "무엇이 생겼고, 어디서 확인하는지, 아직 안 되는 것"만 짧게.

## 하네스 구성 (자동 적용 — 수정 시 주의)

| 겹 | 장치 | 위치 |
|---|---|---|
| 안내 | 세션 시작 상태 주입 / 매 입력 라우팅 | `.claude/hooks/session-context.sh`, `route-prompt.sh` |
| 안내 | 레이어 규칙 (해당 파일 편집 시 자동 로드) | `.claude/rules/{backend,frontend}/` |
| 안내 | 오케스트레이션 스킬 (자동 호출되는 진입점) | `.claude/skills/vibe-{setup,build,run,refactor}/` |
| 안내 | 기술 스킬 (영역별 폴더) | `.claude/skills/{frontend,backend}/` |
| 제약 | 백엔드 경계 테스트 (AST, 래칫) | `backend/tests/architecture/test_boundary.py` |
| 안내 | 데이터 개념 지도 — 세션 시작 시 요약 주입, 설계 0단계 입력 / 자동 생성 ERD | `docs/backend/DOMAIN-MAP.md`, `docs/backend/ERD.md` ← `backend/scripts/gen_erd.py` |
| 제약 | DB 스키마 검사 — 설계(`data-model.yaml`)↔모델 일치 + 정규화 + 테이블 간 중복 의심 (래칫) | `backend/tests/architecture/test_schema.py` |
| 검증 | DB 설계 독립 검증 서브에이전트 — 기존 전체 스키마 대비 중복·결정 기록까지 (spec 단계, PASS 필수) | `.claude/agents/db-design-reviewer.md` |
| 검증 | spec 독립 검증 서브에이전트 — 계약·Task 경계·묶음·이름 규칙·동시 요청 경쟁·기존 e2e 겹침 (병렬 개발 전, PASS 필수) | `.claude/agents/spec-reviewer.md` |
| 검증 | 계약 기계 대조 — spec 「API 설계」 ↔ 실제 서버 (vibe-build 9단계) | `backend/scripts/check_contract.py` |
| 실행 | 서버·화면 개발 서브에이전트 — spec Task 를 묶음별로 나눠 워크트리에서 병렬 spec-run (최대 4개 동시, vibe-build 6단계, 묶음 규칙 `COMMON.md` §5) | `.claude/agents/{backend,frontend}-dev.md`, `scripts/worktree-setup.sh` |
| 제약 | 프론트 계층 import 규칙 | `frontend/eslint.config.mjs` |
| 제약 | 커밋 메시지 형식 검사 (위반 시 커밋 차단 — Claude 는 실행 전, 사람은 git 훅) | `.claude/hooks/commit-msg-check.sh`, `.githooks/commit-msg` → `scripts/check_commit_msg.py` |
| 제약 | 브랜치 흐름 — `main`·`dev` 직접 커밋, main 전환·merge·브랜치 조작, 덮어쓰기 merge 차단 (작업 브랜치에서 커밋 → 검증 후 dev 에 merge, dev → main 은 사람) | `.claude/hooks/git-guard.sh`, `COMMON.md` §3-B |
| 제약 | 민감 정보 커밋 차단 — `.env`·키 파일·비밀값 (git 훅 + CI, 우회 옵션은 Claude 훅이 차단) | `.githooks/pre-commit` → `scripts/check_secrets.py`, `.claude/hooks/git-guard.sh` |
| 제약 | 편집 직후 자동 포맷 | `.claude/hooks/post-edit-format.sh` |
| 제약 | 위험 명령 차단 / 권한 허용 목록 | `.claude/settings.json` |
| 검증 | 화면 실검증 — Playwright MCP 로 눌러보며 콘솔·API 에러 0 → 그 흐름을 e2e 로 고정 (UI Task 필수) | `.claude/skills/frontend/browser-check/SKILL.md` |
| 검증 | 종료 시 품질 게이트 — lint·타입·테스트 + 새 파일 테스트 누락 검사 + 화면 변경 시 e2e (실패하면 종료 차단, 최대 6회) | `.claude/hooks/quality-gate.sh` |
| 검증 | 최종 검증 루프 (정적 + Playwright) | `.claude/skills/vibe-build/harness.md` |
| 정리 | CI / 주간 엔트로피 점검 (데이터 구조 포함) | `.github/workflows/`, `scripts/gc/` |
| 정리 | 쌓인 DB 구조 정리 — 정리안·데이터 영향표 → 사용자 확인 → vibe-build 흐름 (vibe-refactor 가 연결) | `.claude/skills/backend/schema-cleanup/` |

## 기술 스킬 (작업 시작 전에 해당 파일을 읽고 따른다)

| 작업 상황 | 읽을 파일 |
|---|---|
| Zod 스키마·검증 코드 (API 응답, 폼) | `.claude/skills/frontend/zod-usage/SKILL.md` |
| 에러를 toast로 사용자에게 표시 | `.claude/skills/frontend/error-toast/SKILL.md` |
| UI 컴포넌트·페이지 디자인/스타일링 (업무 시스템 디자인 기준) | `.claude/skills/frontend/frontend-design/SKILL.md` + 참고 이미지 `images/` |
| API 엔드포인트 설계·명세 작성 (응답 형태·status·에러표) | `.claude/skills/backend/api-spec/SKILL.md` |
| DB 테이블 추가·변경 (개념 지도·전체 스키마 매핑 → 설계 → `backend/data-model.yaml`) | `.claude/skills/backend/db-design/SKILL.md` |

## 개발 플로우 (진입점 스킬이 내부 절차 스킬을 읽고 따른다)

프로젝트에 슬래시 커맨드는 두지 않는다 — 모든 절차는 스킬이다. 사용자 말에 반응하는 진입점은 최상위 `vibe-*` 4개(setup·build·run·refactor)뿐이고, 단계별 절차는 `.claude/skills/{backend,frontend}/<이름>/SKILL.md` 에 두고 (최종 검증 루프만 `vibe-build/harness.md`) 진입점이 경로로 읽는다 (`backend/spec-run` 표기 = 그 파일). 절차 스킬 공통 규칙(vibe-build 모드·커밋 절차·spec 번호/색인)의 단일 출처는 `.claude/skills/COMMON.md`.

```
vibe-build:    backend/spec-create(API 계약 확정) → frontend/spec-create(그 계약으로) → spec-reviewer → 배치표(묶음 나누기)
               → [backend-dev × 서버 묶음 ∥ frontend-dev × 화면 묶음 — 워크트리, 최대 4개 동시] → 작업 브랜치에 merge
               → backend/sync-api-docs → 계약 대조(check_contract.py)
               → backend·frontend/refactor → backend/verify → frontend/browser-check → vibe-build/harness.md → 검증 반영 커밋 → dev 에 merge
vibe-refactor: (dev 에서 feature/refactor-{slug}) frontend/refactor · backend/refactor (→ 구조 변경 시 vibe-build/harness.md) → 커밋 → dev 에 merge
               DB 구조 정리 요청이면 backend/schema-cleanup (사용자 확인 → vibe-build 흐름)
기타 절차:     backend/verify
```
- **모든 개발 요청(작은 수정·버그 포함)은 spec md 를 남긴다** — 레포 루트 `spec/backend/{NNN}-{기능}.md`, `spec/frontend/{NNN}-{기능}.md`. 번호는 요청 단위로 두 영역이 공유하고, 색인은 `spec/README.md`.
- **기존 기능을 건드리기 전에 `spec/README.md` 에서 관련 spec 을 찾아 읽는다** — 그때 정한 요구사항·결정을 이어받는다.
- 모든 Task 는 테스트를 포함하고, 테스트 실패 상태로 다음 Task 진행 금지. 테스트 약화(skip·삭제·기대값 조작) 금지.
- **코드를 바꾸는 모든 요청은 `dev` 에서 사내 컨벤션 이름의 작업 브랜치를 만들어 작업하고(vibe-build `feature/{NNN}-{slug}`·긴급 `hotfix/{NNN}-{slug}`, vibe-refactor `feature/refactor-{slug}`), 모든 검증(리팩토링·서버·화면·e2e) 통과 후에만 dev 에 merge**한다. `main`·`dev` 직접 커밋은 훅이 차단하고, `dev → main` 은 사람이 직접 한다 (단일 출처 `.claude/skills/COMMON.md` §3-B). `main`·`dev` 는 `make setup` 이 만든다. 워크트리 도우미는 Task 통과마다 커밋 규칙을 읽고 커밋하며, 그 브랜치가 작업 브랜치에 merge 되어 Task 기록이 남는다. merge 도 `-m` 으로 커밋 규칙 형식의 메시지를 준다. 커밋 직전 `docs/CONVENTIONS.md` "### 커밋" 을 읽고, 명시적 경로로만 add(`git add -A` 금지). 형식은 커밋 직전 훅이 검사. **`git push` 금지** (settings 에서 차단).

## 명령 (루트 Makefile)

`make setup` · `make dev` · `make check` · `make e2e` · `make gc` — 상세는 `Makefile` 주석.

## 하지 말 것

- `.env`, `.env.local` 읽기·출력 (차단됨 — 예시는 `.env.example`)
- `known-violations.json` 에 항목 추가 (줄이기만 가능)
- 훅·ESLint 규칙·경계 테스트를 우회하거나 끄기
- 전역 커맨드·스킬 중 이 프로젝트 구조와 다른 것 사용 — 특히 `frontend:migrate-legacy`(4계층 domain·repository·data 기준)·`frontend:convert-frontend-domain`·`setting`. 프론트 구조는 `.claude/rules/frontend/architecture.md`(3계층 Page·Feature·Shared)만 따른다
