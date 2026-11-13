---
name: frontend-spec-create
description: 프론트 화면 요구사항을 spec/frontend/NNN-*.md 작업 계획 문서로 정리하는 절차 (코드 작성 없음). vibe-build 4단계에서 읽는다.
---

# frontend/spec-create — 요구사항을 spec 문서로 정리

> 절차 스킬 — 슬래시 커맨드가 아니다. 표기법·vibe-build 모드·커밋 절차·spec 번호 규칙은 **`.claude/skills/COMMON.md` 를 먼저 읽고** 따른다.

> **vibe-build 모드** — 공통 규칙은 `COMMON.md` §2 (메인에서는 커밋 없음 · 워크트리는 Task별 커밋 · 중간 확인 없음). 이 스킬만의 차이: spec 파일과 색인은 미커밋으로 둔다 (spec-reviewer PASS 후 vibe-build 5단계가 작업 브랜치에 커밋). Task 의 "커밋" 필드는 워크트리·단독 실행용으로 그대로 적는다. UI Task 의 "검증" 필드에는 browser-check 용 URL·흐름을 그대로 적는다 (vibe-build 12단계가 사용).

사용자가 전달한 기능 요구사항을 분석해 **`spec/frontend/` 폴더**(레포 루트의 `spec/` 아래)에 **작업 계획 문서(md)** 를 생성하고, 색인 `spec/README.md` 에 한 줄을 추가한다. 폴더가 없으면 먼저 생성한다.
**모든 개발 요청은 spec 을 남긴다** — 문구·색 하나 바꾸는 작은 수정이나 버그 수정도 예외 없음. 작은 요청은 요구사항 3줄 + Task 1개로 축약해도 된다 (버그면 원인·수정 내용을 요구사항에 적는다).
**이 스킬은 코드를 절대 작성하지 않는다** — 산출물은 spec 문서 하나뿐이다. 구현은 `frontend/spec-run`이 담당.

## 입력 형태

```
frontend/spec-create <기능 요구사항 설명>
```

입력: 이 스킬을 따르라고 지시한 쪽이 넘겨준 내용 (위 형태 중 하나)

---

## 실행 절차

### 1️⃣ 컨텍스트 수집

- 루트 `CLAUDE.md`, `frontend/CLAUDE.md` 를 읽는다.
- 관련 rules(`.claude/rules/frontend/*.md`)와 **API 계약**을 확인한다. 계약 출처:
  - vibe-build 가 짝 서버 spec 을 넘겨줬으면(서버도 이번에 바뀜) 그 spec 의 「API 설계」 섹션 — 서버 구현 전이므로 `swagger/docs.md` 에 섹션이 없어도 정상이다. 「API 의존성」에 "계약: `spec/backend/{NNN}-*.md` API 설계" 와 쓰는 엔드포인트를 적는다.
  - 그 외에는 `frontend/swagger/docs.md` 의 해당 도메인 섹션. 섹션이 없으면 백엔드가 아직 없다는 뜻이므로 멈추고 호출한 쪽에 알린다.
- Task 의 "작업"·"파일"에 파일·컴포넌트·훅·함수 이름을 적을 때는 `.claude/rules/frontend/naming-convention.md` 「폴더·파일」·「계층별 export 이름」을 먼저 읽고 그 규칙대로 짓는다 (`{Domain}Mapper`·`{domain}Service`·`{domain}Keys`·`{domain}{Target}Query`·`useRead*`, 타입 `I`/`T` 접두사). 도우미는 spec 에 적힌 이름을 그대로 쓰므로 여기서 틀리면 코드까지 틀린다.
- 기존 코드 중 이번 기능과 겹치는 부분(같은 도메인의 `features/{domain}/` 등)을 grep으로 파악한다.
- `spec/README.md` 색인에서 이번 기능과 관련된 기존 spec(같은 기능의 이전 작업, `spec/backend/` 의 짝 문서 포함)을 찾아 **읽는다**. 이전 spec 의 요구사항·결정 사항은 이어받고, 바뀌는 점은 이번 spec 에 명시한다.

### 2️⃣ 요구사항 분석

- 요구사항을 **검증 가능한 단위**(FR-1, FR-2, ...)로 쪼갠다. "~할 수 있다" 형태로.
- 모호한 부분은 **추측으로 채우지 말고** 사용자에게 질문한다. 답을 받기 전엔 해당 부분을 "열린 질문" 섹션에 남긴다.
- 이번에 다루지 않을 것을 "범위 제외"에 명시한다.

### 3️⃣ Task 분해

- **Task 1개 = 테스트 가능한 최소 단위 1개.** 레이어·관심사가 다르면 Task를 나눈다.
- `.claude/rules/frontend/architecture.md` 「새 기능 하나가 거치는 파일 (만드는 순서)」 순서대로 아래에서 위로 — 마지막이 `app/{경로}/page.tsx`(import·export만) (각 레이어 rules 문서의 테스트 규칙 준수). AppShell `NAV_ITEMS` 메뉴는 공유 파일이라 화면 Task 에 넣지 않고 아래 「묶음」 규칙대로 `화면-기반` 또는 데이터 묶음 맨 앞의 별도 Task 로 둔다
- **모든 Task에 테스트 코드를 명시한다** — 테스트 파일 경로, 검증 항목, 실행 명령(`pnpm test <경로>` 등). **`pnpm type-check`·`pnpm lint` 같은 기계적 기준은 보조 수단일 뿐, 테스트 코드를 대체할 수 없다.**
  - **UI Task(components/pages)는 렌더링 테스트 + Playwright E2E 테스트를 반드시 명시** — E2E 파일 경로(`e2e/{기능}.spec.ts`)와 실행 명령(`make e2e SPEC=e2e/{기능}.spec.ts`), 검증할 핵심 사용자 흐름을 적는다.
  - 프로젝트에 Playwright E2E 설정(`playwright.config.ts`)이 없으면 **E2E 셋업 Task를 spec 앞부분에 추가**한다.
- **모든 Task에 "검증" 필드를 명시한다** — Task 성격별로:
  - UI Task(components/pages): **`frontend/browser-check` 필수** — 검증 URL(페이지 경로)과 MCP 로 눌러볼 핵심 사용자 흐름(단계 나열)을 적는다. 통과 기준: MCP 실검증(콘솔 error 0 + 실패 API 요청 0, `mcp-check.md` 기록) + 그 흐름을 고정한 e2e 통과. 스크린샷 육안 판정은 기준이 아니다.
  - 비UI Task(types/models/services/queries/store/hooks): `pnpm type-check` 등 기계적 수단.
- **모든 Task에 "커밋" 필드를 명시한다** — `{type}: {요약} (spec {NNN} Task {k})` 형식(type: feat|fix|refactor|test|chore — 허용 type 전체는 `docs/CONVENTIONS.md` "### 커밋")으로 커밋 메시지를 미리 작성. `frontend/spec-run`이 Task 통과 시 이 메시지로 커밋한다.
- Task 간 의존 관계가 순서에 반영되어야 한다 — 앞 Task의 산출물 없이는 뒤 Task를 시작할 수 없게.
- **Task 경계 = 커밋마다 green** — Task 하나를 끝낸 커밋에서 lint·타입·테스트가 통과해야 한다. 타입·시그니처를 바꾸는 Task 는 그 소비자(매퍼·호출부·기존 테스트 데이터)를 **같은 Task** 에서 고친다. 기존 함수를 지우는 일은 호출부를 교체하는 Task 에 둔다.
- **"커밋" type 은 `docs/CONVENTIONS.md` 표대로** — 기능·화면이 늘면 `feat`, 동작 변화 없는 구조 변경만 `refactor`. 한 Task 에 둘이 섞이면 `feat`.
- **모든 Task에 "묶음" 필드를 명시한다** — 기준은 `COMMON.md` §5. 여러 화면이 같이 쓰는 것(`components/ui` 부품, 패키지, `lib/` 공용 함수, `NAV_ITEMS` 메뉴)은 별도 Task 로 빼서 `화면-기반`(쓰는 묶음이 2개 이상일 때) 또는 데이터 묶음 맨 앞에 둔다. types~hooks 는 `화면-{도메인}-데이터`, 화면마다 서로 다른 파일이면 `화면-{도메인}-{화면}` 으로 나눈다 — 화면 Task 의 "파일" 에 공유 파일이 들어가지 않게 한다.
- **한 화면에서 서로 의존하는 요청을 동시에 보내면**(예: 상세 조회 + 조회수 증가) 응답 순서가 바뀌어도 화면 값이 맞게 처리 방법을 Task "작업"에 적는다 — 캐시를 고치는 훅은 "캐시가 아직 없을 때"(무효화·재조회)와 "진행 중인 조회가 옛 값을 덮어쓸 때"(취소)를 다룬다.
- **기존 화면 문구와 겹치는 새 문구**(메뉴·버튼 이름이 기존 이름을 포함 — "게시판" ↔ "게시판 현황")가 있으면 `frontend/e2e/*.spec.ts` 의 해당 선택자를 고치는 일을 마지막 UI Task 의 "검증"에 적는다.
- **테스트는 실제 서버 없이 통과해야 한다** (병렬 개발 중엔 서버가 아직 없다) — services 테스트는 msw 로 계약의 응답을 흉내 내고(테스트 데이터는 계약 예시와 같은 모양), hooks 테스트는 기존 규칙대로 `vi.mock` 으로 service 를 모킹한다 (`hooks-layer.md`).

### 4️⃣ spec 파일 생성

- 번호·파일명·템플릿·상단 메타·색인 갱신은 **`COMMON.md` §4** 대로 한다. 이 스킬의 영역은 `frontend` → `spec/frontend/{NNN}-{기능명}.md`, 색인 줄의 영역 칸에 `frontend`, 상태는 `📝 계획됨`.
- **생성 후 spec 파일과 색인만 커밋** (`COMMON.md` §3): `spec/frontend/{NNN}-{기능명}.md`·`spec/README.md` 를 명시적 경로로 add → `docs: spec {NNN} {기능명} 작성 (spec-create)`. 단, 열린 질문이 남아 사용자 답변으로 spec이 곧 수정될 예정이면 답변 반영 후 커밋한다.

### 5️⃣ 사용자 확인

생성 후 호출한 쪽에 다음을 넘긴다 (사용자는 비개발자 — 명령어를 안내하지 않는다):
- spec 파일 경로
- Task 목록 요약 (번호 + 제목 + 테스트 한 줄)
- 열린 질문이 있으면 강조 — 사용자에게는 화면·동작 기준의 쉬운 말로 바꿔 묻는다

---

## 금지 사항

- ❌ 코드 파일 생성·수정 (spec 문서만 산출)
- ❌ 테스트 없는 Task 작성 — 모든 Task는 기계적으로 검증 가능한 통과 기준 필수
- ❌ 계약(짝 서버 spec 「API 설계」 또는 swagger)·기존 코드 확인 없이 기억·추측으로 API 스키마나 파일 구조 서술
- ❌ 열린 질문이 있는데 임의로 결정하고 진행
