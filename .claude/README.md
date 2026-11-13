# `.claude/` — 하네스 구성 안내

이 폴더는 **Claude Code 가 이 프로젝트에서 일하는 방식**을 정의한다. 비개발자가 말로 요청하면 하네스가 자동으로 설계 → 구현 → 검증 → 커밋까지 끝내도록, 아래 여섯 종류의 장치가 겹겹이 적용된다.

| 종류 | 폴더 | 한 줄 역할 |
|---|---|---|
| 설정 | `settings.json`, `settings.local.json` | 권한 허용·차단 목록, 훅 등록, MCP 서버 |
| 훅 (자동 실행 스크립트) | `hooks/` | 세션 시작·입력·편집·커밋·종료 시점에 자동으로 끼어드는 검사와 안내 |
| 규칙 (파일 편집 시 자동 로드) | `rules/{backend,frontend}/` | 레이어별 코딩 규칙 — 해당 경로의 파일을 만지면 자동 주입 |
| 스킬 (절차서) | `skills/` | 진입점 4개(`vibe-*`) + 영역별 절차·기술 스킬 |
| 서브에이전트 | `agents/` | 워크트리에서 개발하는 도우미 2개 + 읽기 전용 검증자 2개(DB 설계·spec) |
| 템플릿 | `templates/` | spec 문서 양식 |

---

## 1. 폴더·파일 전체 목록

### 1-1. 루트

| 파일 | 역할 |
|---|---|
| `settings.json` | 프로젝트 공통 설정(git 커밋됨). 기본 권한 모드 `acceptEdits`, 허용 명령(make·pnpm·uv·pytest·ruff·alembic·docker compose up/ps/logs·`curl -s http://localhost:*`·git status/diff/log/add/commit/apply/merge/switch/branch/worktree·ls·cat·mkdir 등), 차단 명령(`git push`, `git reset --hard`, `git clean`, `rm -rf`, `docker compose down -v`, `docker volume rm`, `alembic downgrade base`, `.env`·`.env.local` 읽기·편집, `cat/head/tail/less/grep *.env*`), 5개 시점에 훅 스크립트 6개 등록, Playwright MCP 서버 활성화. ※ `cat *.env*` 차단은 `.env.example` 도 잡는다 — 예시 파일은 Read 도구로 읽는다 |
| `settings.local.json` | 개인용 추가 허용 목록. 현재 `python3`, `wc -l`, `head -12 *.md`. ※ 레포 `.gitignore` 에는 없다 — 개인 git 전역 ignore 로만 빠져 있으니 커밋하지 않도록 주의 |
| `README.md` | 이 문서 |

### 1-2. `hooks/` — 자동 실행 스크립트

| 파일 | 실행 시점 | 역할 |
|---|---|---|
| `_lib.sh` | (공용 함수) | 프로젝트 루트·`.harness/` 경로 결정, 개발 환경 준비 여부(`.env`·`.venv`·`node_modules`), DB 실행 여부, 진행 중·멈춘 harness run 목록 |
| `session-context.sh` | SessionStart | 세션 시작 시 현재 상태 주입 — 환경 준비 여부, DB 상태, 변경 파일 수, 최근 커밋 5건, spec 색인 최근 5건, 진행 중/멈춘/오래 방치된 작업. 품질 게이트 기준 커밋(`.harness/session-base`)은 resume·compact 에선 그대로 두고, startup·clear 에서도 **게이트를 통과한 상태일 때만** HEAD 로 앞당긴다 (검증 안 된 커밋이 시야에서 빠지지 않게) |
| `route-prompt.sh` | UserPromptSubmit | 모든 사용자 입력에 라우팅 지시 주입 — 코드 변경이면 vibe-build, 정리면 vibe-refactor, 실행이면 vibe-run, 환경 미준비면 vibe-setup. 사용자가 슬래시 커맨드를 몰라도 하네스가 적용되는 진입점 |
| `git-guard.sh` | PreToolUse(Bash) | ① 민감 정보 검사를 건너뛰는 git 명령 차단 — `git add -f/--force`, `git commit --no-verify/-n`, `core.hooksPath` 변경·해제(`.githooks` 로 설정만 허용). ② 브랜치 흐름(`COMMON.md` §3-B) — `main`·`dev` 위의 commit, main 으로 전환·merge·브랜치 강제 이동/삭제, dev 강제 이동/삭제, 한쪽 덮어쓰기 merge(`-X ours/theirs`·`-s ours`), 한 호출에 브랜치 전환 + commit/merge 를 섞는 것 차단. `git -C 경로` 도 그 경로 브랜치로 판정. python3 가 없으면 git 명령을 막는다 |
| `commit-msg-check.sh` | PreToolUse(Bash) | `git commit`·`git merge` 메시지 첫 줄이 커밋 컨벤션(`feat|fix|design|hotfix|style|refactor|comment|docs|test|chore|rename|remove(scope): 제목`, `!HOTFIX:`, `!BREAKING CHANGE:`)을 따르는지 검사 — `-m`·`-am`·`--message=`·heredoc·`-F 파일` 모두. 메시지 없는 `git merge`(`--ff-only`·`--abort` 등 제외)도 차단. 규칙 단일 출처는 `scripts/check_commit_msg.py` (git `commit-msg` 훅과 공유) |
| `post-edit-format.sh` | PostToolUse(Edit·Write·MultiEdit) | 방금 수정한 파일만 자동 포맷 — Python 은 `ruff check --fix` + `ruff format`, TS/TSX 는 `eslint --fix`. 메인 폴더·워크트리 모두 지원 |
| `quality-gate.sh` | Stop | 작업 종료 시 품질 게이트. 세션 시작 이후 바뀐 `backend/`·`frontend/` 파일이 있으면 바뀐 쪽만 검사: 백엔드 `ruff` + `pytest` + `alembic check`, 프론트 `lint` + `type-check` + `vitest` + **새 파일 짝 테스트 누락 검사** + 화면 변경 시 e2e. 실패하면 종료를 막고 에러를 돌려줘 계속 고치게 한다(최대 6회). 같은 상태로 이미 통과했으면 재검사 생략, `PAUSED` 파일이 있으면 막지 않고 알림만, 진행 중 run(`DONE` 없음)이 있으면 e2e·새 화면 e2e 누락 검사는 최종 검증 루프로 미룬다. 단 `PAUSED`·진행 중 run 은 **최근 24시간 안에 갱신된 것만** 인정한다(`_lib.sh` `RUN_FRESH_MIN`) — 방치된 run 이 검사를 무기한 미루지 못하게. 서버만 바뀌어도 e2e 를 돌린다. python3 가 없으면 검사 불가를 알린다. ※ 작업 폴더 전체의 변경을 보므로, 같은 폴더에서 다른 창이 진행 중인 작업의 파일도 함께 검사된다 |

### 1-3. `rules/` — 레이어별 코딩 규칙 (경로 매칭으로 자동 로드)

각 파일 상단 frontmatter 의 `paths` 에 해당하는 파일을 편집할 때 자동으로 컨텍스트에 들어온다.

**`rules/backend/`** — 4계층 `router → service → repository → models`

| 파일 | 적용 경로 | 역할 |
|---|---|---|
| `python-convention.md` | `backend/**/*.py` | 모든 레이어 공통 — 네이밍·포맷팅·import·주석. 기준은 `docs/backend/CONVENTIONS.md` |
| `router-layer.md` | `domains/*/router.py` | HTTP 입출력 전담 — 파라미터 바인딩, service 호출, envelope 반환 |
| `service-layer.md` | `domains/*/service.py` | 비즈니스 로직 전담, 트랜잭션 경계 소유 |
| `repository-layer.md` | `domains/*/repository.py` | DB 접근 전담 — 쿼리만 알고 비즈니스는 모른다 |
| `model-layer.md` | `domains/*/models.py` | SQLAlchemy 엔티티 규칙 — `data-model.yaml` 과 1:1 일치 |
| `schema-layer.md` | `domains/*/schemas.py` | Pydantic Request/Response DTO 규칙 |
| `exception-handling.md` | `domains/*/exceptions.py`, `app/common/**` | **응답 envelope 스펙의 단일 출처** (성공·페이지·에러 3형식), 예외·핸들러 규칙 |
| `db-design.md` | `models.py`, `data-model.yaml`, `spec/backend/**` | 정규화·설계 일치 규칙 요약. 상세 절차는 `skills/backend/db-design` |
| `test-convention.md` | `backend/tests/**` | pytest 작성 규칙 |

**`rules/frontend/`** — `src/` 3계층 Page · Feature · Shared (사내 FE 컨벤션 반영, 전역 규칙보다 우선)

| 파일 | 적용 경로 | 역할 |
|---|---|---|
| `architecture.md` | `frontend/**` | 프론트 구조의 **단일 출처** — 폴더 책임, import 허용 방향, 계층별 규칙 파일 지도 |
| `naming-convention.md` | `*.ts/tsx/js/jsx` | 변수·함수·타입·React 이름 규칙 (타입 `I`/`T` 접두사) |
| `javascript-convention.md` | `*.ts/tsx/js/jsx` | JS/TS 함수 작성 규칙 |
| `react-convention.md` | `*.tsx`, `hooks/**` | 컴포넌트 폴더 구조(`<PascalCase>/index.tsx`), ui·layout·shared 구분, Page 계층. 6축 기준(단일 책임·선언적·가독성·예측가능성·응집도·결합도) |
| `types-layer.md` | `types/`, `constants/` | 화면 모델 타입(I/T 접두사)과 상수 |
| `models-layer.md` | `models/` | Zod 스키마 + Mapper (ACL·Adapter 계층) |
| `services-layer.md` | `services/` | API 호출 + `safeParse` + Mapper 변환 |
| `queries-layer.md` | `queries/` | queryKey factory + `queryOptions` |
| `hooks-layer.md` | `hooks/` | 읽기 `useRead*`(useQuery), 쓰기 `useCreate/Update/Delete*`(useMutation + invalidate) |
| `store-layer.md` | `store/` | Zustand — 서버 데이터가 아닌 공유 클라이언트 상태만 |
| `axios.md` | `lib/axios.ts`, `services/` | `axiosInstance` 단일 진입점 + interceptor 뼈대. HTTP 호출은 services 에서만 |
| `font.md` | `app/layout.tsx`, `globals.css` | `next/font` 로만 글꼴 임베딩. DesignKit 반입 전엔 글꼴을 건드리지 않음 |

### 1-4. `skills/` — 절차서

**진입점 스킬 4개** — 사용자 말에 반응하는 유일한 입구 (`route-prompt.sh` 가 매 입력마다 안내)

| 폴더 | 트리거 | 역할 |
|---|---|---|
| `vibe-setup/` | 환경 미준비, "설치·준비·처음" | `make doctor` → env 파일 생성 → DB 기동 → 의존성 설치 → 마이그레이션 |
| `vibe-build/` | "만들어줘·추가해줘·바꿔줘·고쳐줘" | 요청 하나를 완성까지 — 0 준비 → 1 요구사항 → 2 범위 → 3 서버 spec(API 계약) → 4 화면 spec → 5 spec 검증(spec-reviewer) + 배치표(묶음) → 6 병렬 개발(서브에이전트·워크트리, 최대 4개, 기반 묶음 마지막 커밋 즉시 다음 출발) → 7 작업 브랜치에 merge → 8 API 문서 → 9 계약 대조(check_contract.py) → 10 리팩토링 → 11 서버 검증 → 12 화면 검증(MCP→e2e) → 13 최종 검증 → 14 검증 반영 커밋 → dev merge → 15 보고 |
| `vibe-build/harness.md` | (vibe-build 13단계, vibe-refactor 4단계가 읽음) | 최종 검증 루프 — `.harness/runs/{slug}/` 에 `task.md`·`state.md` 를 두고 "검사 → 고침" 을 통과까지 반복. 커밋은 하지 않음 |
| `vibe-refactor/` | "정리해줘·리팩토링·중복 줄여줘" | 동작은 그대로, 코드만 정리. `frontend/refactor`·`backend/refactor` 를 읽고 따름 |
| `vibe-run/` | "보여줘·실행해줘·켜줘" | DB 기동 → 백엔드·프론트 백그라운드 실행 → health 확인 → 접속 주소 안내 |

**`skills/COMMON.md`** — 절차 스킬 공통 규칙의 단일 출처: 표기법(`backend/spec-run` = 그 SKILL.md 파일), vibe-build 모드(메인은 커밋 없음·워크트리는 Task별 커밋·중간 확인 없음), 단독 실행도 작업 브랜치에서, 커밋 절차, §3-B 브랜치 흐름(dev → 작업 브랜치 → 검증 후 dev merge), spec 번호·색인 규칙, §5 묶음(병렬 개발 단위 — Task 의 `묶음` 필드, 기반 묶음, 공유 파일 소유).

**`skills/backend/`**

| 폴더 | 종류 | 역할 |
|---|---|---|
| `spec-create/` | 절차 | 요구사항 → `spec/backend/NNN-*.md` 작업 계획 문서 (코드 작성 없음). 테이블 변경이 있으면 `db-design-reviewer` 에이전트 PASS 필수 |
| `spec-run/` | 절차 | spec 의 Task 를 pytest 게이트와 함께 순서대로 구현·커밋 |
| `refactor/` | 절차 | 변경된 백엔드 파일을 `rules/backend` 기준(중복·재사용·가독성·구조)으로 검토, 안전 항목만 수정 |
| `verify/` | 절차 | 서버를 띄워 curl 로 엔드포인트(status·envelope) 실검증, 에러 자동 수정 루프. 남의 리소스 권한(403)은 개발용 일반 사용자 `dev-user` 로 확인하고, 검증용 데이터는 끝나면 지운다 |
| `sync-api-docs/` | 절차 | `app.openapi()` → `frontend/swagger/docs.md` API 계약 문서 생성 (프론트 개발의 입력) |
| `api-spec/` | 기술 | 엔드포인트 설계 — 응답 형태(단건·페이지·커서·생성·삭제), HTTP 메서드·status, 에러 코드표, 명세 템플릿 |
| `db-design/` | 기술 | 0단계(개념 지도·전체 스키마에 매핑 — 확장 vs 신설, 결정 기록) → 엔티티·관계 추출 → 정규화 → `backend/data-model.yaml`. 패턴 카탈로그 포함. `models.py` 작성 전에 끝나야 함 |
| `schema-cleanup/` | 절차 | 쌓인 구조 부채(중복·미사용 테이블) 수집 → 정리안·데이터 영향표 → **사용자 확인** → vibe-build 흐름으로 데이터 이동 마이그레이션. vibe-refactor 가 연결 |

**`skills/frontend/`**

| 폴더 | 종류 | 역할 |
|---|---|---|
| `spec-create/` | 절차 | 화면 요구사항 → `spec/frontend/NNN-*.md`. UI Task 에는 browser-check 용 URL·흐름 기록 |
| `spec-run/` | 절차 | spec 의 Task 를 vitest 게이트와 함께 순서대로 구현·커밋 |
| `refactor/` | 절차 | 변경된 프론트 파일 검토 — 공통 컴포넌트 추출, 함수 길이, 변수 가독성, Next.js 경계 |
| `browser-check/` | 절차 | Playwright MCP 로 실제 브라우저를 눌러보며 콘솔·API 에러 0 확인 → 그 흐름을 `frontend/e2e/{기능}.spec.ts` 로 고정. UI Task 완료 전 필수. "내 글만" 같은 권한 화면은 `dev-user` 데이터로 확인, e2e·MCP 가 만든 데이터는 끝나면 API 로 삭제(`test.afterEach` + `request`) |
| `frontend-design/` | 기술 | 사내 업무 시스템 디자인 기준 — 주황 단일 강조색, 절제된 회색, 표·폼 중심 |
| `frontend-design/images/` | 참고 | 디자인 기준 스크린샷을 넣는 곳 (현재 비어 있음, 넣는 법·따르지 않을 부분 표는 `README.md`) |
| `zod-usage/` | 기술 | API 응답·요청은 `safeParse` + `DomainLayerError`, 폼은 react-hook-form 과 `parse`. 섞어 쓰지 않음 |
| `error-toast/` | 기술 | 에러를 toast 로 보여줄 때 — 백엔드 메시지 vs 프론트 정의 메시지 선택, `@/lib/toast` 단일 경로. 디자인 킷 Toast 도입 전엔 표시 부품 미연결 |

### 1-5. `agents/` — 서브에이전트

| 파일 | 도구 | 역할 |
|---|---|---|
| `backend-dev.md` | Read·Write·Edit·Bash·Grep·Glob | vibe-build 6단계. 별도 워크트리에서 백엔드 spec 의 맡은 묶음 Task 를 rules 대로 구현(여러 개 병렬, 공유 파일은 기반 묶음만), Task 통과마다 커밋, 브랜치명 보고. 규칙·spec 은 항상 메인 경로 최신본을 읽음 |
| `frontend-dev.md` | Read·Write·Edit·Bash·Grep·Glob | vibe-build 6단계. 별도 워크트리에서 프론트 spec 의 맡은 묶음 Task 구현(여러 개 병렬). API 계약은 짝 서버 spec 「API 설계」(서버도 새로 만들 때) 또는 메인의 `frontend/swagger/docs.md`, 서버 없이 msw 로 테스트 |
| `db-design-reviewer.md` | Read·Grep·Glob (읽기 전용) | spec 의 "데이터 모델" yaml 을 요구사항·기존 전체 스키마와 대조해 정규화·누락·관계 오류, 기존 테이블 중복, 결정 기록 검증. PASS/FAIL 만 판정. 사람 리뷰를 대신하는 유일한 설계 검증 |
| `spec-reviewer.md` | Read·Grep·Glob (읽기 전용) | vibe-build 5단계. 서버·화면 spec 짝의 계약 완전성·Task 경계(커밋마다 green)·이름 규칙·커밋 type·묶음 나누기·동시 요청 순서 경쟁·기존 e2e 선택자 겹침 검증. PASS/FAIL 만 판정 |

### 1-6. `templates/`

| 파일 | 역할 |
|---|---|
| `spec-template.md` | spec 문서 양식 — 상태(📝 계획됨/🚧 진행중/✅ 완료), 대상 영역, 관련 도메인, 짝 문서, 관련 spec, 요구사항·데이터 모델·API·Task 섹션 |

---

## 2. 적용된 하네스 (겹별 정리)

| 겹 | 장치 | 위치 | 동작 |
|---|---|---|---|
| **안내** | 세션 시작 상태 주입 | `hooks/session-context.sh` | 환경·DB·변경 파일·최근 커밋·spec 색인·진행 중 작업 |
| 안내 | 매 입력 라우팅 | `hooks/route-prompt.sh` | 요청 종류에 따라 vibe-* 스킬로 보냄 |
| 안내 | 레이어 규칙 자동 로드 | `rules/**` | 해당 경로 편집 시 규칙 주입 |
| 안내 | 오케스트레이션 스킬 | `skills/vibe-*` | 설계→개발→검증→커밋 절차 |
| **제약** | 위험 명령 차단 / 권한 허용 | `settings.json` | push·hard reset·rm -rf·볼륨 삭제·.env 접근 차단 |
| 제약 | 커밋 메시지 형식 검사 | `hooks/commit-msg-check.sh` + git `.githooks/commit-msg` → `scripts/check_commit_msg.py` | Claude 커밋은 실행 전, 사람 커밋은 git 훅에서 차단 |
| 제약 | 브랜치 흐름 | `hooks/git-guard.sh`, `skills/COMMON.md` §3-B | dev 에서 작업 브랜치 → 검증 후 dev 에 `--no-ff -m` merge. main·dev 직접 커밋, main 조작, 덮어쓰기 merge 차단. `dev → main` 은 사람만 |
| 제약 | 민감 정보 커밋 차단 | `.githooks/pre-commit` → `scripts/check_secrets.py`, `hooks/git-guard.sh`, CI `secrets` job | `.env`·키 파일·비밀값 스테이징 시 커밋 차단, 우회 옵션(`-f`·`--no-verify`·hooksPath 변경)은 Claude 훅이 차단 |
| 제약 | 편집 직후 자동 포맷 | `hooks/post-edit-format.sh` | ruff / eslint --fix |
| 제약 | 백엔드 경계 테스트 (AST, 래칫) | `backend/tests/architecture/test_boundary.py` | 레이어 간 import 방향 위반 검출. `known-violations.json` 은 줄이기만 가능 |
| 안내 | 데이터 개념 지도 / ERD | `docs/backend/DOMAIN-MAP.md`, `docs/backend/ERD.md` (`backend/scripts/gen_erd.py`) | 세션 시작 훅이 개념 요약 주입, 설계 0단계 입력 |
| 제약 | DB 스키마 검사 (래칫) | `backend/tests/architecture/test_schema.py` | `data-model.yaml` ↔ `models.py` 1:1 일치 + 정규화 + 테이블 간 중복 의심(`schema-similar-tables`). 미사용 테이블(`schema-unused-table`)은 `make gc` 보고 |
| 제약 | 프론트 계층 import 규칙 | `frontend/eslint.config.mjs` | Page·Feature·Shared import 방향 |
| **검증** | DB 설계 독립 검증 | `agents/db-design-reviewer.md` | spec 단계에서 PASS 필수 |
| **검증** | spec 독립 검증 | `agents/spec-reviewer.md` | 병렬 개발 전 PASS 필수 |
| **검증** | 계약 기계 대조 | `backend/scripts/check_contract.py` | spec 「API 설계」 ↔ 실제 서버, 9단계 |
| 검증 | 서버 실검증 | `skills/backend/verify` | curl 로 status·envelope 확인 |
| 검증 | 화면 실검증 → e2e 고정 | `skills/frontend/browser-check` + Playwright MCP | 콘솔·API 에러 0 → `frontend/e2e/*.spec.ts` |
| 검증 | 종료 시 품질 게이트 | `hooks/quality-gate.sh` | lint·타입·테스트·테스트 누락·e2e, 실패 시 종료 차단(최대 6회) |
| 검증 | 최종 검증 루프 | `skills/vibe-build/harness.md` | `.harness/runs/{slug}/state.md` 기반 반복 |
| **실행** | 워크트리 개발 서브에이전트 | `agents/{backend,frontend}-dev.md`, `scripts/worktree-setup.sh` | 묶음별로 분리된 폴더에서 병렬로 Task별 커밋 → 합치기 → 계약 대조 |
| **정리** | CI / 주간 엔트로피 점검 | `.github/workflows/{ci,gc}.yml`, `scripts/gc/check.sh` | 민감 정보 검사, 백엔드 ruff + `alembic upgrade head`·`alembic check` + pytest, 프론트 lint+tsc+vitest+build. (e2e·테스트 누락 검사는 로컬 Stop 게이트만) |

### 하네스가 남기는 상태 파일 (`.harness/`, git 미커밋)

| 경로 | 쓰는 쪽 | 용도 |
|---|---|---|
| `.harness/session-base` | `session-context.sh` | 품질 게이트가 "이 세션에서 바뀐 파일" 을 계산하는 기준 커밋 |
| `.harness/gate-count` / `gate-pass` / `gate-last.log` | `quality-gate.sh` | 차단 횟수, 통과한 변경 지문, 마지막 실패 로그 |
| `.harness/runs/{slug}/task.md`, `state.md`, `PAUSED`, `DONE` | vibe-build, harness.md | 작업 원문, 현재 상태(병렬 개발이면 배치표 포함), 사용자 답 대기 표시, 완료 표시 |
| `.harness/runs/{slug}/log.md` | harness.md | 최종 검증 바퀴별 기록 (덧붙이기만) |
| `.harness/runs/{slug}/console-errors.log` | `frontend/e2e/fixtures.ts` | e2e 중 브라우저 콘솔·런타임 에러. 최종 검증이 바퀴마다 비우고 `[console.error]`·`[pageerror]` 로 시작하는 줄만 센다 |
| `.harness/runs/{slug}/mcp-check.md` | browser-check | Playwright MCP 실검증 결과 기록 |
| `.harness/playwright-mcp/` | Playwright MCP | 스크린샷·트레이스 출력 |

---

## 3. 기본 인프라

| 항목 | 내용 |
|---|---|
| 구조 | 모노레포 — `frontend/`(Next.js) + `backend/`(FastAPI), 공통 문서 `docs/`, 요청별 기록 `spec/` |
| DB | PostgreSQL 16 (`backend/docker-compose.yml`, 볼륨 `postgres_data`, healthcheck `pg_isready`, 기본 포트 5432 — 충돌 시 `make db-port PORT=…`) |
| 마이그레이션 | Alembic (`backend/alembic/`), 품질 게이트에서 `alembic check` 로 모델↔마이그레이션 일치 검사 |
| 패키지 관리 | 백엔드 `uv` + `.venv`(Python ≥ 3.11, CI 는 3.12), 프론트 `pnpm` |
| 실행 | 백엔드 `uvicorn app.main:app --reload --port 8000`, 프론트 `next dev`, health `GET /api/health` |
| 개발용 사용자 | `backend/scripts/seed_dev_user.py`(`make setup` 이 실행, 다시 실행해도 중복 없음) — `dev-admin`(staff, 빈 DB 에서 id 1, 프론트 `NEXT_PUBLIC_DEV_USER_ID`) + `dev-user`(일반, 권한 검증용 `X-User-Id`) |
| git 훅 | `.githooks/pre-commit` (민감 정보 검사) — `make setup` 이 `core.hooksPath` 를 설정 |
| 브라우저 자동화 | Playwright MCP `@playwright/mcp@0.0.83` (chromium, headless) — 루트 `.mcp.json`, `settings.json` 에서 활성화 |
| 작업 폴더 격리 | `git worktree` (`.claude/worktrees/<이름>`) + `scripts/worktree-setup.sh` 로 env·venv·의존성 준비 |
| CI | GitHub Actions `ci.yml` (민감 정보·백엔드·프론트 3 job), `gc.yml` (주간 점검) |
| 명령 모음 | 루트 `Makefile` — `doctor` · `setup` · `db` · `db-port` · `dev` · `dev-backend` · `dev-frontend` · `check` · `check-backend` · `check-frontend` · `e2e` · `gc` · `worktree-setup` |

---

## 4. 라이브러리

### 백엔드 (`backend/pyproject.toml`)

| 용도 | 라이브러리 |
|---|---|
| 웹 프레임워크 | FastAPI ≥ 0.104, Uvicorn[standard] |
| ORM · 마이그레이션 | SQLAlchemy 2.0, Alembic, psycopg2-binary |
| 검증 · 설정 | Pydantic 2, pydantic-settings, email-validator |
| 인증 | python-jose[cryptography], passlib[bcrypt], bcrypt, python-multipart |
| 테스트 | pytest, pytest-asyncio(`asyncio_mode = auto`), pytest-cov, httpx |
| 린트 · 포맷 | ruff (line-length 120, 규칙 `E F I B UP`, `B008` 제외) |
| 기타 | taskipy(`dev`·`test`·`lint`·`export-docs`), pyyaml(스키마 검사용) |

### 프론트엔드 (`frontend/package.json`)

| 용도 | 라이브러리 |
|---|---|
| 프레임워크 | Next.js 16.2, React 19.2, TypeScript 5 |
| 서버 상태 | @tanstack/react-query 5, @lukemorales/query-key-factory |
| 폼 | react-hook-form 7, @hookform/resolvers (zod 연결) |
| HTTP · 검증 | axios 1.18, zod 3.25 |
| UI | shadcn 4, radix-ui, lucide-react, class-variance-authority, cn |
| 스타일 | Tailwind CSS 4 (`@tailwindcss/postcss`), tw-animate-css |
| 단위 테스트 | vitest 4, @testing-library/react, @testing-library/dom, jsdom, msw 2 |
| e2e | @playwright/test 1.61, playwright-core |
| 린트 | eslint 9, eslint-config-next |

> 클라이언트 전역 상태는 규칙(`rules/frontend/store-layer.md`)상 Zustand 를 쓰기로 되어 있으나, 아직 의존성에는 없다. 첫 store 를 만들 때 추가한다.

---

## 5. 수정할 때 주의

- 훅·ESLint 규칙·경계 테스트를 **우회하거나 끄지 않는다**. `known-violations.json` 은 항목을 줄이기만 한다.
- 규칙이 바뀌면 `rules/` 의 해당 파일을 고치고, 문서(`docs/`)는 참고용으로 둔다. 단일 출처가 정해진 것(envelope → `exception-handling.md`, 프론트 구조 → `architecture.md`, 절차 공통 → `skills/COMMON.md`)은 그 파일만 고친다.
- 프로젝트 `.claude/rules/**`·`skills/**` 는 전역 `~/.claude/` 의 같은 이름보다 **우선**한다.
- 슬래시 커맨드는 두지 않는다 — 모든 절차는 스킬이고, 진입점은 `vibe-*` 4개뿐이다.
