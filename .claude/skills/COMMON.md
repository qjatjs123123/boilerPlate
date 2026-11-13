# 절차 스킬 공통 규칙

`.claude/skills/{backend,frontend}/*/SKILL.md` 중 절차 스킬(spec-create·spec-run·refactor·verify·sync-api-docs·browser-check)과 그 스킬을 부르는 쪽(vibe-* 진입점, backend-dev·frontend-dev 에이전트)이 함께 따르는 규칙의 **단일 출처**. 각 스킬에는 이 파일과 다른 점만 적는다.

---

## 1. 표기·호출

- 절차 스킬은 **슬래시 커맨드가 아니다** — 진입점 스킬(`vibe-build`·`vibe-refactor` 등)이나 다른 절차 스킬이 파일을 **읽고 따른다**. 같은 이름의 전역 커맨드(`~/.claude/commands`)가 목록에 보여도 이 프로젝트의 파일이 우선한다.
- `frontend/refactor`·`backend/spec-run` 같은 표기는 `.claude/skills/{영역}/{이름}/SKILL.md` 파일을 뜻한다.
- 사용자는 비개발자다 — 명령어·슬래시 커맨드를 안내하지 않는다. 물어야 하면 화면·동작 기준의 쉬운 말로 묻는다.

## 2. vibe-build 모드

vibe-build 가 절차 스킬을 따르게 한 경우다. 각 스킬의 「vibe-build 모드」 문단은 여기에 **더해지는 그 스킬만의 차이**이며, 그 스킬의 단독 실행 규칙보다 우선한다.

- **하위 스킬은 메인 폴더에서 커밋하지 않는다** — 스킬 안의 커밋 단계(문서·Task·완료 커밋)를 모두 건너뛴다. 고친 파일은 미커밋 상태로 두고 보고에 목록을 남긴다. 메인 폴더의 커밋은 vibe-build 만 한다 — 모두 **작업 브랜치**(§3-B, `feature/{NNN}-{slug}`)에: 워크트리 방식은 spec 커밋(5단계)·도우미 브랜치 merge(7단계)·검증 반영 커밋(14단계)을 쌓고, 직접 방식은 14단계에 커밋 1회. 모든 검증 후 **dev 에 merge 1회**(14단계).
- **워크트리(backend-dev·frontend-dev)에서는 Task 통과마다 §3 절차로 커밋한다** — 이 커밋들은 7단계 merge 로 기록에 그대로 남는다. spec 문서는 수정·커밋하지 않고(최신본은 메인 경로), 체크박스·상태는 Task별 결과(커밋 해시 포함)를 보고로 넘겨 메인이 갱신한다.
- **워크트리 도우미는 맡은 묶음(§5)의 Task 만 한다** — 여러 도우미가 동시에 돌므로 묶음 밖 파일·공유 파일은 고치지 않고 보고로 넘긴다. 기반 브랜치를 받았으면 그 위에서 시작한다.
- **중간에 사용자 확인을 받지 않는다** — 요구사항은 vibe-build 1단계에서 확정됐다. 단독 실행용 "사용자에게 보여주고 진행" 단계는 건너뛰고, 판단이 필요한 것은 호출한 쪽에 보고한다.
- 리팩토링(10단계)·서버 실검증(11단계)·화면 MCP 검증(12단계)은 vibe-build 의 해당 단계가 맡는다 — spec-run 은 Task 구현 + 테스트까지만.

## 2-B. vibe-refactor 모드

vibe-refactor 가 `frontend/refactor`·`backend/refactor` 를 따르게 한 경우다.

- 하위 refactor 스킬의 **완료 커밋을 건너뛴다** — 수정 파일은 미커밋으로 두고 목록만 넘긴다. 커밋은 vibe-refactor 4단계가 검증 통과 후 1회.
- 1️⃣ 의 파일 목록 확인과 "수동 확인 필요" 항목의 사용자 확인은 vibe-refactor 2단계가 쉬운 말로 대신 묻는다.

## 2-C. 단독 실행

위 두 모드가 아닌 경우(사용자가 절차 스킬 하나만 요청) 각 스킬 본문의 커밋·확인 단계를 그대로 따른다.
- **커밋이 있는 스킬이면 시작 전에 §3-B 1번으로 작업 브랜치를 만든다** (`feature/{NNN}-{slug}` — spec 번호가 없는 작업이면 `feature/{slug}`). `main`·`dev` 위의 커밋은 훅이 막으므로, 스킬 본문의 "완료 커밋"은 항상 작업 브랜치에 쌓이고 모든 검증 통과 후 §3-B 3번으로 dev 에 merge 한다.

## 3. 커밋 절차

커밋·merge 할 때마다 (vibe-build 의 spec·merge·검증 반영·dev merge, vibe-refactor 커밋·dev merge, 워크트리 Task 커밋, 단독 실행 커밋 모두 — `git merge` 는 반드시 `-m` 으로 같은 형식의 메시지를 준다):

**vibe-build 흐름의 모든 커밋(spec·Task·묶음 합치기·도우미 `fix:`·검증 반영·dev merge)은 첫 줄 끝에 `(spec {NNN})` 을 붙인다** — 뒤의 refactor `--spec`·vibe-refactor 가 `git log --grep="(spec {NNN}"` 로 이 표시를 찾아 바뀐 파일을 모은다. 빠지면 그 커밋의 파일은 리팩토링 대상에서 조용히 누락된다.

1. `docs/CONVENTIONS.md` 의 "### 커밋" 절을 **Read** 한다 — 기억으로 쓰지 않는다. 워크트리에서는 `{메인}/docs/CONVENTIONS.md`.
2. 메시지가 그 규칙에 맞는지 확인한다. spec Task 의 "커밋" 필드가 있으면 그 메시지를 확인하고, 틀리면 규칙대로 고친다.
3. 이번 범위의 파일만 **명시적 경로로** `git add` 한다 — `git add -A`·`git add .` 금지, `.harness/` 제외.
4. 커밋한다. 커밋 직전 훅이 형식을 거부하면 규칙대로 고쳐 다시 커밋한다. `git push` 금지.

## 3-B. 브랜치 흐름 — dev 기준 작업 브랜치 → 검증 후 dev 에 merge

코드를 바꾸는 진입점(vibe-build·vibe-refactor, schema-cleanup 은 vibe-build 흐름)이 따른다. 브랜치 이름은 `docs/CONVENTIONS.md` "### 브랜치"(사내 컨벤션).

| 브랜치 | 역할 |
|---|---|
| `main` | 배포 가능 상태. 하네스는 건드리지 않는다 — `dev → main` 반영은 사람이 직접 |
| `dev` | 개발 기준. 작업 브랜치는 여기서 갈라지고, 검증 통과 후 여기로 merge |
| `feature/{NNN}-{slug}` | vibe-build 기능 추가·변경·버그 수정 (NNN = spec 번호) |
| `hotfix/{NNN}-{slug}` | 사용자가 "급하다·긴급"이라고 한 수정 |
| `feature/refactor-{slug}` | vibe-refactor 코드 정리 |

1. **시작** — `dev` 가 없으면 vibe-setup(`make setup`)으로 만든다. `git switch dev` 후 `git status --porcelain` 확인:
   - 비어 있으면 그대로 진행.
   - 커밋 안 된 이전 변경이 있으면 쉬운 말로 1번 묻는다 — "저장되지 않은 이전 작업이 있어요. 이번 작업에 함께 넣을까요, 따로 보관해 둘까요?" "함께" → 그대로 새 브랜치로 가져간다. "보관" → `git stash push -u -m "vibe: {slug} 시작 전 보관"` 후 진행하고 보고에 "이전 작업은 따로 보관해 두었어요"를 넣는다. (`git switch dev` 가 미커밋 변경 때문에 실패하면 전환 전에 같은 질문을 한다 — "함께"면 지금 브랜치에서 `git stash push -u` → `git switch dev` → 새 브랜치에서 `git stash pop`.)
   - `git switch -c {작업 브랜치}` — 브랜치명은 run 의 `state.md` 에 적고, 재개할 때는 그 브랜치로 `git switch` 해서 잇는다.
2. **커밋** — 작업 브랜치에만 (§3 절차). `main`·`dev` 위의 `git commit` 은 `git-guard` 훅이 막는다. 훅은 **명령 실행 전 브랜치**로 판정하므로 브랜치 전환과 커밋은 **별도 Bash 호출**로 한다.
3. **dev 에 merge** — 모든 검증 통과 후에만: `git switch dev` → `git merge --no-ff {작업 브랜치} -m "{type}({도메인}): {요약} (spec {NNN})"`(§3 형식 — vibe-build 는 첫 줄 끝 `(spec {NNN})` 필수, vibe-refactor 는 `refactor: {요약}`) → `git branch -d {작업 브랜치}`. 충돌하면 `git merge --abort` 후 작업 브랜치로 돌아가 사용자에게 보고한다 (한쪽 덮어쓰기 금지). 검증 실패로 끝나면 merge 하지 않고 작업 브랜치에 남겨 둔다.

## 4. spec 번호·파일·색인

- **번호는 요청(기능) 단위로 backend·frontend 가 공유한다.** 호출한 쪽(vibe-build)이 넘겨주면 그대로 쓴다. 넘겨받지 못했으면 같은 요청의 짝 문서(`spec/{반대 영역}/{NNN}-*.md`) 번호·기능명을 쓰고, 그것도 없으면 `spec/backend/`·`spec/frontend/` **두 폴더를 합친** 최대 번호 + 1 (첫 파일은 `001`).
- 파일: `spec/{backend|frontend}/{NNN}-{kebab-case-기능명}.md` (폴더가 없으면 생성). 템플릿 `.claude/templates/spec-template.md` 의 구조를 그대로 따른다. 상단 메타에 `짝 문서`(있을 때)와 `관련 spec`(같은 기능의 이전 작업)을 적는다.
- 색인 `spec/README.md` — 없으면 아래 형식으로 만들고, 이번 spec 한 줄을 표 맨 아래에 추가한다. 같은 번호 줄이 이미 있으면 그 줄의 영역 칸에 이번 영역을 덧붙인다.

  ```markdown
  # spec 색인
  개발 요청마다 하나의 번호. 기존 기능을 고치기 전에 여기서 관련 spec 을 찾아 읽는다.

  | 번호 | 영역 | 기능 (화면·동작 기준 한 줄) | 관련 코드 | 관련 spec | 상태 | 날짜 |
  |---|---|---|---|---|---|---|
  | 001 | backend, frontend | 공지사항 목록·작성 | domains/notice, features/notice | — | 📝 계획됨 | 2026-10-05 |
  ```
- 상태 값: `📝 계획됨` → `🚧 진행중` → `✅ 완료` (spec 문서와 색인 줄을 함께 갱신).

## 5. 묶음 — 병렬 개발 단위

vibe-build 6단계는 spec Task 를 **묶음** 단위로 도우미에게 나눠 준다. 묶음 하나 = 도우미 하나 = 워크트리 하나. 같은 묶음 안의 Task 는 순서대로(직렬), 묶음끼리는 기반 관계만 지키면 동시에 돈다.

### 묶음 종류

| 영역 | 묶음 | 담는 Task | 기반 묶음 |
|---|---|---|---|
| 서버 | `서버-기반` | 모든 도메인의 models Task(`data-model.yaml`·models.py·마이그레이션·`alembic/env.py`) + 새 도메인의 빈 `router.py`(prefix·tags 만 둔 `APIRouter`) + `app/main.py` 라우터 등록 | — |
| 서버 | `서버-{도메인}` | 그 도메인의 repository → service → router → 통합 테스트 | `서버-기반` (있으면) |
| 화면 | `화면-기반` | 여러 묶음이 같이 쓰는 것: `components/ui/*` 부품 추가, 패키지 추가(`package.json`·lock), `lib/` 공용 함수, `AppShell.tsx` `NAV_ITEMS` 메뉴 | — |
| 화면 | `화면-{도메인}-데이터` | types → constants → models → services → queries → store → hooks | `화면-기반` (있으면) |
| 화면 | `화면-{도메인}-{화면}` | 그 화면의 components → pages → `app/{경로}/page.tsx` (예: `목록`, `작성`, `상세`) | `화면-{도메인}-데이터` |

### 나누는 기준 — 작업 폴더 준비(1~2분/개)보다 이득이 클 때만

- 영역(서버·화면)에 묶음이 1개만 나오면 나누지 않는다 — 그 영역의 Task 전부를 묶음 하나(`서버-{도메인}` / `화면-{도메인}-데이터`)에 담는다. 이때 기반 Task 도 같은 묶음 맨 앞에 두고, **그 묶음이 공유 파일의 소유자**다 (아래 「공유 파일」의 "기반 묶음" = 이 묶음).
- `서버-기반` 은 **서버 도메인 묶음이 2개 이상**일 때만 따로 둔다 (마이그레이션은 DB 를 공유하므로 반드시 한 도우미가 만든다).
- `화면-기반` 은 그 공용 Task 를 쓰는 화면 묶음이 2개 이상일 때만 따로 둔다.
- 화면별 묶음(`화면-{도메인}-{화면}`)은 그 도메인 화면이 **2개 이상이고 서로 다른 파일**일 때만 나눈다. 아니면 데이터 묶음에 화면 Task 까지 담는다.
- 한 도메인의 서버 Task 는 나누지 않는다 (층마다 앞 층 결과가 필요하고 구간이 짧다).

### 묶음별로 고치면 안 되는 파일 (공유 파일)

아래는 기반 묶음(기반 묶음을 따로 두지 않았으면 그 영역의 유일한 묶음)만 고친다. 다른 묶음에서 바꿔야 할 일이 생기면 고치지 말고 보고의 **공유 파일 요청**에 적는다 — 메인이 7단계 합치기 뒤에 반영한다.
- 서버: `backend/data-model.yaml`, `app/domains/*/models.py`, `alembic/versions/*`, `alembic/env.py`, `app/main.py`, `app/common/**`, `app/core/**`, `pyproject.toml`
- 화면: `components/ui/*`, `components/layout/*`, `lib/*`, `package.json`, `pnpm-lock.yaml`, 다른 도메인의 `features/*`, 같은 도메인이라도 다른 화면 묶음의 components·pages
- 마이그레이션 생성·`alembic upgrade` 는 마이그레이션을 담은 묶음만 한다.

### 기반 브랜치에서 시작

기반 묶음이 있으면 도우미는 워크트리 준비 전에 `git merge --ff-only {기반 커밋 해시}` 로 기반 결과를 가져온다 (호출자는 기반 도우미의 **마지막 Task 커밋**이 생기는 즉시 그 해시로 위 묶음을 띄운다 — 기반 도우미의 마무리 검사를 기다리지 않는다). 기반 브랜치는 메인 HEAD 에서 갈라진 워크트리 브랜치이므로 항상 fast-forward 된다 — 실패하면 작업하지 말고 보고한다.
작업 중 호출자가 "기반에 fix 커밋이 생겼다"고 알리면 `git merge {기반 브랜치} -m "chore: 기반 묶음 fix 반영 (spec {NNN})"` 로 받는다 (충돌하면 `git merge --abort` 후 보고). 메인은 기반 묶음부터 차례로 작업 브랜치에 merge 하므로 겹치는 커밋은 git 이 한 번만 합친다.

### spec 표기

Task 마다 `**묶음**: {묶음 이름}` 필드를 적는다 (`.claude/templates/spec-template.md`). spec-create 가 위 기준으로 정하고, vibe-build 5단계가 이 필드로 배치표를 만든다. 같은 묶음의 Task 는 spec 에서 연속으로 둔다.
