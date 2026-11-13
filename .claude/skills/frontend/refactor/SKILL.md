---
name: frontend-refactor
description: 변경된 프론트 파일(React/Next.js)을 .claude/rules/frontend 기준으로 검토 — 공통 컴포넌트 추출, 함수 길이·변수 가독성, 구조, Next.js 경계 — 하고 안전 항목만 수정하는 절차.
---

# frontend/refactor — 변경된 파일 리팩토링 검토

> 절차 스킬 — 슬래시 커맨드가 아니다. 표기법·vibe-build 모드·커밋 절차·spec 번호 규칙은 **`.claude/skills/COMMON.md` 를 먼저 읽고** 따른다.

> **vibe-build 모드** — 공통 규칙은 `COMMON.md` §2 (하위 스킬은 커밋 없음 · 워크트리는 Task별 커밋 · 중간 확인 없음). 이 스킬만의 차이: 대상은 호출자가 정한다 — 워크트리 방식은 `--spec {NNN}`(도우미 Task 커밋이 작업 브랜치에 merge 되어 남아 있다) **+ 워킹트리 미커밋 변경**을 합친 목록, 직접 방식은 **워킹트리 변경 파일**(기본 모드). 적용한 수정은 커밋하지 않는다 (vibe-build 14단계 검증 반영 커밋에 포함). 1️⃣ 의 파일 목록은 보여주지 않고 진행하며, 이번 요청과 무관해 보이는 파일은 검토에서 빼고 보고에만 남긴다.

`git`으로 식별한 **현재 변경된 파일**을 `.claude/rules/frontend/` 기준으로 검토하고 개선안을 제시한다.

**우선순위 (이 순서대로 본다):**
1. **중복 최소화** — 같은 로직/마크업이 두 곳 이상에서 반복되는지
2. **재사용성** — 추출하면 다른 곳에서도 쓸 수 있는 단위인지
3. **가독성** — 위→아래 한 흐름으로 읽히는지, 시점 이동·매직 넘버·복잡 조건 없는지
4. **구조 개선** — 단일 책임, 레이어 경계, 합성/훅 분리
5. **Next.js 경계** — Server/Client 경계, Next 내장 부품(`Link`·`Image`·`dynamic`·`metadata`) 사용

이 5가지가 1순위. 그 외 룰(네이밍·타입 등)은 발견되면 부수적으로 보고하되 우선 다루지 않는다.

---

## 입력 형태

- `frontend/refactor` — **검토만**. 위반 사항과 제안을 출력하고 끝. 자동 수정 안 함.
- `frontend/refactor --apply` — 의미가 명확하고 안전한 항목만 Edit 도구로 직접 수정. 구조 변경(컴포넌트 분리·hook 추출 등)은 항상 제안만 하고 사용자 확인 후 진행.
- `frontend/refactor --spec {NNN}` — 워킹트리 대신 **해당 spec의 커밋들이 변경한 파일**을 대상으로 검토. `--apply`와 조합 가능 (`frontend/spec-run` 완료 시퀀스와 vibe-build 10단계 워크트리 방식이 `--spec {NNN} --apply` 로 호출).
- `frontend/refactor {파일·폴더 경로...}` — 지정한 파일 또는 폴더 아래 코드 전체를 검토 (예: "공지사항 화면 정리해줘" → `frontend/src/features/notice/`).

---

## 실행 절차

### 1️⃣ 변경 파일 수집

인자에 따라 수집 방식이 갈린다:

- **인자 없음 (기본)** — 워킹트리의 변경 파일:
  ```bash
  git status --porcelain
  git diff --name-only HEAD
  ```
- **`--spec {NNN}`** — 해당 spec의 커밋들이 변경한 파일 (Task 단위 커밋 후 워킹트리가 깨끗한 상태용):
  ```bash
  git log --grep="(spec {NNN}" --name-only --pretty=format: | sort -u
  ```
  커밋 메시지 형식 `{type}: {요약} (spec {NNN} Task {k})` 를 전제로 한다. spec 번호는 backend·frontend 가 공유하므로 아래 경로 필터(frontend 코드만)로 이 영역 파일만 남긴다. 매칭 커밋이 0개면 사용자에게 알리고 종료.
- **파일·폴더 경로 인자** — 파일은 그대로, 폴더는 그 아래 `.ts/.tsx` 전부.

수집 방식과 무관하게 아래 필터를 동일하게 적용한다:
- modified / untracked / staged 모두 포함
- 확장자: `.ts`, `.tsx`, `.js`, `.jsx` 만 (md/json/lock/yml 제외)
- 경로: 프론트엔드 코드만 — 모노레포면 `frontend/` 이하, 프론트 단독 레포면 프로젝트 루트 기준
- 제외: `node_modules/`, `.next/`, `dist/`, `build/`, `coverage/`

결과가 **0개**면 "변경된 코드 없음"으로 정상 종료.

수집 후 사용자에게 파일 목록을 먼저 보여주고 진행한다 — 의외의 파일이 포함되면 멈출 수 있게.

### 2️⃣ 파일 경로 → 적용 룰 매핑

| 파일 경로 패턴 | 적용 룰 |
|---|---|
| `features/*/pages/**`, `features/*/components/**`, `app/**/*.tsx`, `components/**` | `architecture.md` + `react-convention.md` + `javascript-convention.md` |
| `features/*/hooks/**`, `hooks/**` | `hooks-layer.md` + `react-convention.md` + `javascript-convention.md` |
| `features/*/queries/**`, `queries/**` | `queries-layer.md` + `javascript-convention.md` |
| `features/*/store/**`, `store/**` | `store-layer.md` + `javascript-convention.md` |
| `features/*/services/**`, `services/**` | `services-layer.md` + `javascript-convention.md` |
| `features/*/models/**`, `models/**` | `models-layer.md` + `javascript-convention.md` |
| `features/*/types/**`, `types/**` | `types-layer.md` + `javascript-convention.md` |
| `lib/axios.ts`, `lib/axios/**` | `axios.md` + `javascript-convention.md` |
| 그 외 `.ts/.tsx` | `javascript-convention.md` |

룰 파일은 `.claude/rules/frontend/{name}.md` 로 읽는다.
`naming-convention.md`(변수·함수·타입 네이밍)는 모든 `.ts/.tsx` 파일에 공통 적용한다.

### 3️⃣ 우선순위별 검토

**변경 파일 안만 보지 말 것** — 중복·재사용성은 *다른 파일*과 비교해야 보인다. `frontend/src/features/**`, `frontend/src/components/**`, `frontend/src/{lib,utils,hooks,services,queries,constants}/**` 를 grep으로 함께 확인.

#### 🥇 1순위: 중복 최소화
- **동일/유사 로직 반복** — 같은 fetch+state 패턴, 같은 조건 분기, 같은 변환 함수가 변경 파일과 기존 파일에 같이 있는지 확인.
  - 발견 방법: 함수 시그니처·핵심 키워드(`axios.get`, `useQuery`, 도메인 이름)로 grep.
- **동일/유사 JSX 마크업 반복** — `map` 안의 카드/리스트 아이템, 모달 레이아웃, 로딩 스켈레톤이 여러 곳에서 비슷하게 반복되는지.
- **단, "지금 중복" ≠ "추상화 대상"** — `react-convention §결합도`의 "중복 허용" 원칙을 지킨다: **갈라질 가능성이 있으면 통합 권장하지 않는다**. 진짜 항상 같이 바뀔 코드만 추출 후보.
- **상수·매직 값 중복** — 같은 숫자/문자열이 여러 파일에 박혀 있으면 공용 `src/constants/` 또는 도메인 `constants/{domain}Constants.ts`로 추출.

#### 🥈 2순위: 재사용성
- **추출하면 다른 곳에서도 쓸 수 있는 단위인가**:
  - 컴포넌트 안에 정의된 보조 함수 중 **순수**하고 도메인 무관이면 공용 `src/utils/`로 (예: `utils/formatDate.ts`).
  - 도메인 무관 React 로직(스크롤·미디어쿼리·debounce)은 전역 `hooks/`로.
  - 도메인 로직이면 `features/{domain}/utils/`로.
- **공통 컴포넌트로 뺄 수 있는가** — 반복 마크업을 어디로 올릴지는 쓰는 범위로 정한다 (`react-convention.md` 「ui · layout · shared」):
  | 쓰는 범위 | 추출 위치 |
  |---|---|
  | 한 컴포넌트 안에서만 반복 | 같은 폴더 안 하위 부품 (`{Name}/BoardRow.tsx`) |
  | 같은 도메인의 여러 컴포넌트 | `features/{domain}/components/<Name>/index.tsx` |
  | 두 번째 도메인이 실제로 필요해짐 | `components/shared/<Name>/index.tsx` — 데이터는 props·config 주입, `features/` import 금지 |
  | 버튼·체크박스·다이얼로그 같은 원자 UI | 직접 만들지 말고 shadcn `components/ui/*` 재사용 (없으면 `pnpm dlx shadcn@latest add`) |
  - 지금 한 도메인만 쓰는데 "언젠가 쓸 것 같아서" shared 로 올리지 않는다.
  - 직접 만든 `<button>`·`<input type="checkbox">`·`window.confirm` 이 보이면 shadcn 부품 교체 제안.
- **props 인터페이스가 너무 좁아 재사용 불가**한 컴포넌트 — 도메인 타입을 강하게 박지 말고 필요한 필드만 받게 설계 권장.
- **컴포넌트가 children/slot props를 받지 않아 합성 불가** — 같은 레이아웃을 두 곳에서 다르게 쓰려면 `children`이나 slot으로 열어둬야 한다.

#### 🥉 3순위: 가독성
- **함수 길이** — 15줄 초과면 분리 검토 (`javascript-convention`).
- **JSX 중첩 깊이 3~4단계+** — 하위 컴포넌트 추출.
- **중첩 삼항** — IIFE + 순차 `if` 패턴.
- **복잡 조건** — `isSameCategory` 같은 이름 있는 변수로 추출.
- **매직 넘버/문자열** — 상수로.
- **시점 이동** — 단순 분기를 외부 상수 파일로 빼서 추적이 어려워졌으면 컴포넌트 내부 `switch`로 회수.
- **early return 누락** — 가드를 본문 앞으로.
- **함수 분리 방법** — 15줄 초과 함수는 "무엇을 하는가"를 한 문장으로 쓰고, 단계(검증·변환·호출 등)마다 이름 있는 함수로 나눈다. 인자 3개 초과면 객체 인자로 (`javascript-convention`).
- **변수·함수 이름** — `data`·`temp`·`item2`·`flag` 같은 뜻 없는 이름, 축약어(`usr`, `cnt`), boolean 인데 `is/has/can` 접두사 없음, 핸들러가 `handleXxx`/`onXxx` 규칙 위반 → 역할이 드러나는 이름 제안 (`naming-convention.md`).
- **한 변수 재활용** — 같은 `let` 을 다른 의미로 재할당 → 의미별 `const` 로 분리.

#### 4순위: 구조 개선
- **단일 책임 위반** — 컴포넌트가 페칭+상태+렌더링을 한꺼번에. → custom hook으로 로직 분리.
- **레이어 경계 위반** — 도메인 내부 의존 방향(`architecture.md` 「도메인 내부 의존 방향」) 역행, `queries/`에 `useQuery`/`useMutation` 호출, 컴포넌트에서 service 직접 호출, Service에 `queryClient`, `app/` 페이지에 화면 조합(import·export만 허용) 등.
- **Effect 남용** — 파생 state 동기화, props→state 동기화 (`useEffect` 제거하고 렌더 중 계산 또는 `key` reset).
- **컴포넌트 안에 컴포넌트 정의** — 매 렌더 재생성, 모듈 최상위로.
- **거대 hook** — `usePageState`처럼 책임이 여러 개면 분리.
- **Props Drilling 3단계+** — ① 합성(`children`) → ② Context 순서로 해결 제안.
- **`isLoading`/`isError`를 표시 컴포넌트에 prop으로** — `QueryBoundary`로 흡수.

#### 5순위: Next.js 경계 (App Router)
근거: `react-convention.md` 「Server vs Client Component 경계」·「Page Layer」, `architecture.md`, `font.md`.
- **`'use client'` 위치** — 훅(`useState`·`useEffect`·`use*`)·이벤트 핸들러·브라우저 API(`window`·`document`·`localStorage`)가 **0건인 파일**에 `'use client'` 가 있으면 제거 제안. 반대로 큰 부모 전체에 붙어 있고 상호작용은 일부 자식뿐이면, 상호작용 부분만 잎 컴포넌트로 떼고 거기에 선언.
- **서버 컴포넌트에서 브라우저 API** — `'use client'` 없는 파일에서 `window`·`document`·`localStorage` 접근 → 렌더 에러. 잎 클라이언트 컴포넌트로 옮긴다.
- **`app/**/page.tsx`** — `features/*/pages/<X>Page` import + `export default` + `metadata` 만 (`app/layout.tsx` 는 예외 — `ReactQueryProvider`·`AppShell` 감싸기와 글꼴만, `architecture.md` §1). 화면 조합·훅 호출·스타일이 있으면 도메인 `pages/` 로 이동 제안. `metadata` 는 `page.tsx`/`layout.tsx` 에만 (클라이언트 컴포넌트에선 무효).
- **`<a href="/내부경로">`** → `next/link` 의 `Link` (클라이언트 전환·prefetch). 외부 URL·`mailto:`·다운로드 링크는 그대로.
- **`<img>`** → `next/image` 의 `Image` (`width`/`height` 또는 `fill` + `alt` 필수). 아이콘은 lucide-react.
- **무거운 클라이언트 전용 부품**(차트·에디터·지도 등, 첫 화면에 안 보이는 모달) → `next/dynamic` 지연 로드 검토. 측정 근거 없으면 제안만.
- **서버 선조회** — 첫 화면을 서버에서 채우는 경우 `pages/<X>Page.tsx`(서버 컴포넌트)에서 `prefetchQuery` + `HydrationBoundary` 패턴인지, 서버 컴포넌트가 service 결과를 props 로 직접 내리고 있지 않은지 (캐시 이중화).
- **글꼴** — `<link>`·CSS `@import` 로 웹폰트를 불러오면 `next/font`(`font.md`)로.
- **`src/pages/` 폴더 생성 금지** — Pages Router 와 충돌.

### 4️⃣ 보고서 출력 형식

우선순위 라벨(🥇🥈🥉4️⃣5️⃣)을 붙여 사용자가 한눈에 중요도를 보게 한다.

```
## features/post/components/PostCard/index.tsx
**적용 룰**: react-convention, javascript-convention

🥇 중복 최소화
- features/post/components/PostListItem/index.tsx 와 카드 마크업(line 12-28) 거의 동일
  → 공통 `<PostThumbnail>` 추출 검토 (단, 향후 리스트 카드가 갈라질 가능성 확인 필요)

🥈 재사용성
- `formatRelativeTime` 함수가 이 파일에 인라인 — 도메인 무관 순수 함수
  → `utils/formatDate.ts` 이동 권장

🥉 가독성
- 22줄 함수 `handleSubmit` — 검증/제출 분리 권장
- key={index} — post.id로 교체 (자동 수정 가능)

4️⃣ 구조 개선
- useEffect로 `fullName` 동기화 → 렌더 중 계산 (자동 수정 가능)
- 데이터 페칭과 렌더링이 한 컴포넌트에 있음 → `useReadPost` 훅으로 분리 검토

5️⃣ Next.js 경계
- `'use client'` 선언됐지만 훅·이벤트 0건 → 제거 (자동 수정 가능)
- `<a href="/posts">` → `Link` (자동 수정 가능)
```

마지막에 요약:
```
## 요약
- 검사 파일: 5개
- 🥇 중복: 3건  🥈 재사용성: 2건  🥉 가독성: 6건  4️⃣ 구조: 4건  5️⃣ Next.js: 2건
- 자동 수정 가능: 5건 / 수동 확인 필요: 10건
- `frontend/refactor --apply` 로 자동 수정 항목만 적용 가능
```

### 5️⃣ `--apply` 모드

`frontend/refactor --apply` 호출 시 **안전 항목만** Edit 도구로 수정.

자동 수정 OK:
- 매직 넘버 → 상수 (같은 파일 내 상수 선언)
- 의미 없는 `<div>` → `<></>` (스타일·이벤트 없을 때만)
- `key={index}` → 안정적 ID (ID 후보가 명확할 때만)
- 인라인 조건 → 이름 있는 변수 추출
- 중첩 삼항 → IIFE + if
- 사용 안 하는 import 제거
- `useEffect`로 파생값 동기화 → 렌더 중 계산 (의존성·side effect 없는 명백한 경우만)
- 불필요한 `'use client'` 제거 (그 파일에 훅·이벤트 핸들러·브라우저 API 0건이고, import 하는 자식이 클라이언트 전용 훅을 쓰지 않을 때만)
- 내부 경로 `<a href="/...">` → `Link` (href 가 `/` 로 시작하는 고정 내부 경로일 때만)
- 지역 변수·private 함수 이름 개선 (export 되지 않아 외부 영향이 없을 때만)

자동 수정 **금지** (제안만):
- 컴포넌트/훅 추출, 파일 이동
- 중복 코드 통합 (갈라질 가능성 사용자 판단 필요)
- 레이어 경계 변경 (mutation → hooks/ 이동 등)
- 외부 시그니처(props, 반환 타입) 변경
- `<img>` → `Image`, `next/dynamic` 도입 (레이아웃·로딩 동작이 바뀜 — 화면 확인 필요)
- 비즈니스 로직 변경

수정 후 다시 보고서를 출력해 어떤 항목이 적용됐는지 명시.

**완료 커밋**: 수정 항목이 1건 이상이고 `pnpm test` + `pnpm type-check`가 통과하면 수정 파일만 **명시적 경로로 `git add`** 후 `refactor: {대상 요약} (frontend/refactor --apply)` 메시지로 커밋한다 (`git add -A` 금지, push 금지). 테스트 실패 시 커밋하지 않고 보고한다.
단, **커밋을 관장하는 다른 스킬이 호출한 경우**(예: `frontend/spec-run` 완료 시퀀스의 `--spec {NNN}` 호출, vibe-build 10단계, vibe-refactor — `COMMON.md` §2·§2-B)에는 직접 커밋하지 않고 호출자의 커밋 규칙에 맡긴다.

---

## 안전 가드

- **변경 파일 50개 초과** 시 진행 전 사용자 확인.
- **테스트 파일** (`*.test.ts(x)`, `*.spec.ts(x)`)은 별도 섹션, 우선순위 1~2(중복/재사용)만 가볍게 본다.
- **자동 생성 파일**(`.next/`, `coverage/`, lock)은 무시.
- **중복 통합 제안은 반드시 "갈라질 가능성" 한 줄 평가를 동반** — react-convention 결합도 원칙.

---

## 출력 규칙

- 위반 0건 파일은 `✅ 위반 없음`만 표시.
- 각 항목에 **룰 출처**(`[react-convention §결합도]` 등)를 적어 근거 추적 가능하게.
- 코드 제안은 가능하면 diff 블록으로.
- 1순위(중복)·2순위(재사용성) 항목이 가장 위, 3·4·5순위는 그 아래.
