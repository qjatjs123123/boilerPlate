---
description: React 컴포넌트/페이지/훅 작성 시 — 컴포넌트 폴더 구조(<PascalCase>/index.tsx), ui·layout·shared 구분, Page 계층
paths:
  - "**/*.tsx"
  - "**/hooks/**/*.ts"
---

# React 컴포넌트 작성 규칙

이 문서는 좋은 React 컴포넌트를 만들기 위한 규칙이다. 컴포넌트를 작성하거나 수정하기 전에 반드시 읽고 따른다.

기준은 **단일 책임 · 선언적 · 가독성 · 예측가능성 · 응집도 · 결합도** 6축이다. 모두 한꺼번에 만족하긴 어렵다 — 상황에 맞게 우선순위를 판단한다.

> **이 프로젝트 전용 (사내 FE 컨벤션 반영)** — 전역 `~/.claude/rules/frontend/react-convention.md` 와 다르면 이 파일이 우선한다.

## 컴포넌트 선언 (사내 컨벤션)

- 이름은 **PascalCase**. 컴포넌트 폴더도 PascalCase 이고 본체는 `index.tsx`, 폴더 안 하위 부품 파일은 PascalCase (`{Name}/BoardTable.tsx`).
- **named export** (`export function PostListSection()`). `export default` 는 `app/**/page.tsx`·`layout.tsx` 에서만.
- `function` 선언 / `const` + 화살표 함수 **둘 다 허용** — 용도에 맞게. 단 **`const` + 화살표 함수로 만들면 `displayName` 을 지정**한다 (DevTools·에러 스택에서 이름 보존):
  ```tsx
  export const BoardRow = ({ row }: IBoardRowProps) => { /* ... */ };
  BoardRow.displayName = 'BoardRow';
  ```
  `forwardRef`·`memo` 로 감싼 컴포넌트도 `displayName` 필수.
- props 는 **구조분해(`{ a, b }: IProps`) / `props: IProps` 둘 다 허용**. 한 파일 안에서는 한 방식으로 통일.
- Props 타입 이름은 `I{Component}Props` / `T{Component}Props` (`naming-convention.md`).

## 컴포넌트 위치·폴더 구조 (사내 FE 아키텍처)

```
src/app/{경로}/page.tsx                            # Page Layer — import·export 만
src/features/{domain}/pages/{Domain}Page.tsx       # 도메인 페이지 화면
src/features/{domain}/components/{Domain}Section/
├── index.tsx                                      # 컴포넌트 본체 ({Domain}Section)
├── {domain}{Name}Config.ts                        # 이 컴포넌트 전용 config·훅 어댑터 (예: noticeBoardConfig.ts, JSX 포함 시 .tsx)
└── __tests__/{Domain}Section.test.tsx
src/components/ui/button.tsx                       # shadcn 순수 UI
src/components/layout/QueryBoundary.tsx            # 앱 골격·경계
src/components/shared/{Name}/index.tsx             # 도메인 공용 복합 컴포넌트 (필요할 때만)
```

### Page Layer — `src/app/` 은 라우팅만
`app/{경로}/page.tsx` 는 **`features/<도메인>/pages/<X>Page` 를 import 해서 `export default` 만** 한다 (+ `metadata`). 화면 조합·훅 호출·스타일은 도메인 `pages/` 에서. `app/` 이 `features/` 중 `pages/` 외 폴더(components·hooks 등)를 import 하면 ESLint 에러. 공용 계층(`@/lib/ReactQueryProvider`, `@/components/layout/AppShell` 등)은 `app/layout.tsx` 에서 사용 가능.

아래 코드는 **가상의 `notice`(공지사항) 기능 기준 예시**다 (실제 파일 없음).

```tsx
// src/app/notice/page.tsx
// 페이지 계층 — 라우팅만 담당. 화면은 features/notice/pages/NoticePage
import { NoticePage } from '@/features/notice/pages/NoticePage';

export const metadata = { title: '공지사항' };

export default NoticePage;
```

```tsx
// src/features/notice/pages/NoticePage.tsx
import { NoticeBoardSection } from '../components/NoticeBoardSection';

/** 공지사항 페이지 */
export function NoticePage() {
  return <NoticeBoardSection />;
}
```

`src/pages/` 폴더는 만들지 않는다 (Next.js Pages Router 와 충돌).

### 컴포넌트 폴더 — `<PascalCase>/index.tsx`
- 컴포넌트 1개 = 폴더 1개. 폴더명 = 컴포넌트명(PascalCase), 본체 코드는 `index.tsx`. import 는 폴더 경로 (`'../components/{Domain}Section'`).
  - **예외**: `components/ui/*`(shadcn CLI 생성)와 `components/layout/*`(`AppShell.tsx`·`QueryBoundary.tsx` 같은 앱 골격 단일 파일)은 평평한 파일로 둔다.
- 그 컴포넌트만 쓰는 하위 부품·config·전용 훅·타입(`{name}Type.ts`)·`__tests__/` 는 **같은 폴더 안**에 둔다 (응집도).
- `index.tsx` 는 컴포넌트 본체다 — 다른 파일을 모아 re-export 하는 배럴로 쓰지 않는다.

### ui · layout · shared · 도메인 components 구분

| 위치 | 무엇 | 데이터 |
|---|---|---|
| `components/ui/` | shadcn 원자 부품 (button, checkbox, table …) | props 만 |
| `components/layout/` | 앱 뼈대·경계 (`AppShell`, `QueryBoundary`) | props·children 만 |
| `components/shared/<Name>/` | 여러 도메인이 재사용하는 복합 컴포넌트 (예: 게시판형 목록) | **props·config 주입**으로만 — `features/` import 금지 |
| `features/<도메인>/components/<Name>/` | 한 도메인 전용 컴포넌트 | 도메인 `hooks/` 로 서버 데이터 사용 |

- 한 도메인에서만 쓰면 shared 로 올리지 않는다. 두 번째 도메인이 필요해질 때 shared 로 승격.
- shared 컴포넌트에 도메인을 연결하는 예 (**가상의 `notice` 기능과 공용 `BoardSection` 기준 — 실제 파일 없음**): `NoticeBoardSection` 이 `BoardSection` 에 모듈 레벨 상수 `NOTICE_BOARD_CONFIG`(컬럼·훅 어댑터 `useBoardPage`·`useBulkDelete`)를 주입한다. config 는 렌더마다 새로 만들지 않는다 (rules of hooks).

```tsx
// src/features/notice/components/NoticeBoardSection/index.tsx
'use client';

import { BoardSection } from '@/components/shared/BoardSection';

import { NOTICE_BOARD_CONFIG } from './noticeBoardConfig';

/** 공지 게시판 — 공통 BoardSection에 notice config 주입 */
export function NoticeBoardSection() {
  return <BoardSection config={NOTICE_BOARD_CONFIG} />;
}
```

### 서버 데이터 접근
컴포넌트는 서버 데이터를 **도메인 `hooks/`(`useRead*`·`useCreate*` …)로만** 사용한다. `services/` 직접 호출·`@/lib/axios` import 금지 (`hooks-layer.md`, `axios.md`).

---

## UI 라이브러리 — shadcn/ui

- **버튼·체크박스·셀렉트·테이블·스켈레톤·다이얼로그 등 기본 UI 는 직접 만들지 않는다** (확인창도 `window.confirm` 대신 shadcn `AlertDialog`) — `@/components/ui/*` (shadcn/ui, Radix 기반) 를 쓴다. 없는 부품은 `cd frontend && pnpm dlx shadcn@latest add <부품>`.
- `src/components/ui/` 는 CLI 생성 코드 — 이 문서·`naming-convention.md` 규칙의 **예외**로 원본 형태를 유지한다. 수정은 variant 추가 정도만.
- 색은 하드코딩하지 않고 shadcn 변수 클래스(`bg-primary`, `border-input`, `text-muted-foreground`) 또는 앱 토큰(`text-app-*`)을 쓴다. 클래스 병합은 `cn()`.
- 테스트: Radix 부품은 역할이 다르다 — Checkbox 는 `aria-checked`, Select 트리거는 `combobox`(jsdom 에선 `keyDown Enter` 로 열기). jsdom 폴리필은 `frontend/vitest.setup.ts`.
- 색·모서리 변경은 `src/app/globals.css` 의 shadcn 변수(`--primary`, `--border` …)로만. 이 변수들은 앱 토큰(`--color-app-*`)에 연결돼 있다 (주황 = primary).

## 화면 규칙 (사내 컨벤션)

- **데이터를 보여주는 화면은 로딩 / 에러 / 빈 목록 / 정상 네 상태를 모두 처리**한다 — `QueryBoundary` + 빈 상태 문구.
- **버튼·안내·에러 문구는 한국어.** 에러 표시는 `error-toast` 스킬 기준.
- **스타일은 Tailwind 클래스만** — 별도 CSS 파일·CSS Module·inline style 금지. 색·간격은 `src/app/globals.css` 토큰 사용.
- **클릭 영역 최소 44×44px** (버튼·링크·체크박스 등 터치 대상). 보이는 크기가 아니라 **누를 수 있는 영역** 기준이다 — 16px 체크박스·아이콘 버튼도 패딩·`label`·표 셀 전체 클릭으로 영역을 44px 로 확보하고, 보이는 모양은 `frontend-design` 스킬(촘촘한 표, `size-4` 아이콘)을 따른다.
- **아이콘은 lucide-react** 만 사용 (다른 아이콘 라이브러리 추가 금지).
- 공용으로 쓰일 코드(공용 컴포넌트·훅·util·lib)는 **주석 필수** — "왜"를 쓴다 (`javascript-convention.md`).

---

## 핵심 원칙

### 1. 단일 책임 원칙 (Single Responsibility)
- 하나의 컴포넌트는 하나의 책임만 가진다.
- "이 컴포넌트가 무엇을 하는가?"를 한 문장으로 설명할 수 없다면 분리한다.
- 데이터 페칭, 비즈니스 로직, 렌더링이 한 컴포넌트에 섞여 있으면 분리를 고려한다.

### 2. 적절한 길이 유지
- **진짜 기준은 "책임 한 문장"** — 줄 수는 참고치다. 책임이 한 문장으로 떨어지면 길어도 OK, 짧아도 두 가지 일을 하면 분리.
- 참고치: 본문 로직이 150줄을 넘으면 검토. 한 컴포넌트가 다루는 개념이 6~7개를 넘으면 분리.
- JSX 중첩 깊이 3~4단계 이상이면 하위 컴포넌트로 추출한다.
- 한 함수 안에서 여러 `if/else`로 전혀 다른 UI를 그리고 있다면 컴포넌트를 나눈다.

### 3. 선언적으로 작성
- "어떻게(how)"가 아니라 "무엇을(what)" 보여줄지 표현한다.
- 명령형 DOM 조작(`document.querySelector`, 직접 ref 조작) 대신 상태와 props로 UI를 표현한다.
- 조건부 렌더링은 의도가 드러나게 작성한다. 복잡한 삼항 연산자 중첩은 변수나 컴포넌트로 분리한다.
- **Effect로 상태 동기화하지 않는다** — props가 바뀔 때마다 state를 따라가게 하는 effect는 거의 항상 안티패턴. 파생값은 렌더 중 계산, prop으로 state 리셋이 필요하면 `key` prop으로.

### 4. State 최소화
- **파생값은 state로 만들지 않는다** — props·기존 state로 계산 가능하면 렌더 중 계산. `useState` + `useEffect`로 동기화 금지.
- **state는 쓰는 곳 가까이** — 공유가 필요할 때만 끌어올린다(lift). 기본은 내려놓기(push down).
- **불변 업데이트** — `setItemList([...itemList, x])`. `push`/`splice`로 직접 mutate 금지.
- 단일 진실 공급원 — 같은 데이터를 두 state에 두지 않는다.

### 5. Effect 절제 ("You Might Not Need an Effect")
- **사용자 입력 처리** → 이벤트 핸들러. effect 아님.
- **파생값 계산** → 렌더 중 계산. effect 아님.
- **prop 바뀌면 state 리셋** → `key` prop으로 컴포넌트 재마운트. effect 아님.
- **Effect는 외부 시스템 동기화 전용** — 구독, 타이머, 비-React DOM, 분석 이벤트.
- **1 effect = 1 동기화** — 여러 관심사 묶지 말 것. 의존성 배열 정직하게(린트 끄지 않는다). cleanup 필수.

### 6. 예측 가능성 (이름 ↔ 동작 일치)
- **이름이 같으면 동작이 같아야 한다** — 라이브러리를 감싸 동작을 추가했다면 이름을 바꾼다. 예: 토큰을 자동 첨부하는 `http.get`은 `httpService.getWithAuth`로.
- **같은 류 함수는 반환 타입을 통일한다** — 비슷한 hook 둘 중 하나는 Query 객체, 다른 하나는 data만 반환하지 않는다. 검증 함수는 `{ ok: true } | { ok: false; reason: string }` 같은 discriminated union으로 통일.
- **숨은 부수효과 금지** — 함수 시그니처에 드러나지 않는 로깅·전송·전역 변경을 안에서 수행하지 않는다. 호출부로 옮긴다.

### 7. 가독성
- props, 상태, 핸들러, 렌더링 순으로 일관된 구조를 유지한다.
- **early return으로 가드** — `if (!user) return null;` 먼저. 본문은 정상 케이스만.
- **복잡한 조건은 변수로 추출** — `const isSameCategory = ...; const isPriceInRange = ...;`. 본문은 `return isSameCategory && isPriceInRange;`.
- **중첩 삼항 → IIFE + 순차 if** — `(() => { if (a && b) return 'BOTH'; if (a) return 'A'; ... })()`.
- **시점 이동 줄이기** — 단순한 분기는 외부 상수 파일로 빼지 말고 컴포넌트 안 `switch`로. 위→아래 한 흐름으로 읽히게.
- 매직 넘버/문자열은 상수로 추출한다. 함께 바뀌어야 할 값일수록 더 그렇다(응집도).
- 핸들러·콜백 이름은 `naming-convention.md` 「React」.

### 8. 응집도 (함께 바뀌는 코드는 가까이)
- **도메인 단위로 묶는다** — `features/{domain}/` 안에 pages·components·hooks·queries·services·models·types 가 함께. 공용(`src/components/shared`, `src/hooks`)은 정말 여러 도메인이 쓸 때만.
- **컴포넌트 전용 파일은 컴포넌트 폴더 안에** — config·하위 부품·전용 훅·테스트를 `<Name>/` 폴더에 모은다.
- **폼 응집도 선택** — 필드가 독립적이고 재사용된다면 **필드 단위 검증**(react-hook-form 등). 한 비즈니스 단위로 함께 검증돼야 한다면 **폼 전체 schema**(zod) 단위. 폼 검증 코드는 `zod-usage` 스킬을 따른다.
  > react-hook-form·`@hookform/resolvers` 는 설치돼 있다 (예: `features/post` 의 글 작성 폼).

### 9. 결합도 (느슨하게)
- **무리한 추상화보다 중복이 낫다** — 두 곳에서 비슷해 보여도 향후 갈라질 가능성이 있으면 합치지 않는다. "옵션 인자가 폭발하기 시작하면 추상화가 잘못된 신호".
- **Props Drilling 해소 순서**: ① 합성(`children`)으로 깊이 축소 → ② 그래도 안 되면 Context. Props가 컴포넌트 역할을 드러내므로 Context는 최후 수단.

### 10. Server vs Client Component 경계 (Next.js App Router)
- 기본은 Server Component. `'use client'`는 상호작용/브라우저 API/상태가 필요할 때만.
- `'use client'`를 트리 위쪽에 박지 않는다 — 가장 아래(잎)에서 선언해 클라이언트 번들 최소화.
- DB·시크릿 접근은 Server Component에서만.
- **서버 데이터 조회는 기본이 클라이언트 `hooks/`** (`QueryBoundary` 로 로딩 처리). 첫 화면을 서버에서 미리 채워야 할 때만(사내 Q7 getServerSideProps 대응) 도메인 `pages/{X}Page.tsx`(서버 컴포넌트)에서 `queryClient.prefetchQuery({ ...{domain}PageQuery(params) })` 후 `<HydrationBoundary state={dehydrate(queryClient)}>` 로 감싼다. 하위 클라이언트 컴포넌트는 그대로 같은 `useRead*` 훅으로 읽는다 — 서버 컴포넌트에서 service 결과를 props 로 직접 내려주지 않는다 (캐시 이중화 방지).

### 11. 접근성(a11y) 최소선
- 시맨틱 태그 우선 (`<button>`, `<nav>`, `<header>`). `<div onClick>` 금지.
- `<label htmlFor>` ↔ `<input id>` 연결. 이미지 `alt` 필수.
- 키보드로도 동작해야 한다 — 포커스 가능 요소만 클릭 가능하게.
- 시맨틱 태그로 표현할 수 없는 `div` 위젯에는 `role` + `aria-*` 를 붙인다 (사내 컨벤션). 입력 요소는 `<label>` 연결이 기본, 화면에 라벨을 둘 수 없는 디자인이면 `aria-label` 로 무엇을 입력하는지 알린다. `placeholder` 는 예시 문구일 뿐 라벨을 대신하지 않는다.
- 점검 도구: axe, Lighthouse. `eslint-plugin-jsx-a11y` 는 도입 보류.

### 12. 성능은 측정 후 최적화
- 기본은 `memo`/`useMemo`/`useCallback` 없이 작성한다.
- 프로파일러로 병목을 확인한 뒤에만 메모이제이션. 비싼 계산만 `useMemo`.
- 리스트 가상화는 행 수가 수백을 넘을 때만.

---

## 컴포넌트 패턴과 사용 시점

### 표시 컴포넌트 + Custom Hook (구 Presentational / Container)
**언제:** 데이터를 가져오는 로직과 보여주는 로직이 섞일 때.
- **표시 컴포넌트(Presentational)**: props만 받아 UI를 그린다. 상태 거의 없음.
- **로직은 Custom Hook으로 추출** — `useReadPost`, `useCreatePost` 같이. "Container 컴포넌트"라는 별도 래퍼는 만들지 않는다(과거 패턴, 현재는 hook으로 충분).
- 효과: 표시 컴포넌트는 재사용·테스트·Storybook 작성이 쉬워진다.

### Custom Hook으로 로직 추출
**언제:** 컴포넌트 안에 상태 관리·부수효과·복잡한 계산 로직이 쌓일 때, 또는 같은 로직이 여러 컴포넌트에 반복될 때.
- `useXxx` 형태로 로직만 분리해 컴포넌트는 렌더링에 집중하게 한다.
- 데이터 페칭, 폼 상태, 타이머, 이벤트 구독 등은 우선적으로 훅으로 분리한다.
- **거대 hook 만들지 말 것** — 한 hook이 여러 책임을 지면 쪼갠다. 쿼리 파라미터 여러 개를 한 `usePageState`로 묶지 말고 파라미터당 hook 하나.
- 반환은 객체 또는 튜플 일관성. 인자 3개 초과면 객체로 (`javascript-convention.md`).
- 효과: 컴포넌트가 짧아지고 선언적이 되며, 로직을 독립적으로 테스트할 수 있다.

### Compound Component (합성 컴포넌트)
**언제:** 여러 하위 요소가 하나의 맥락을 공유하면서 유연한 조합이 필요할 때 (예: `<Tabs>`, `<Accordion>`, `<Select>`).
- 부모가 Context로 상태를 공유하고, 자식들이 그 상태를 소비한다.
- `<Tabs><Tabs.List><Tabs.Tab/></Tabs.List><Tabs.Panel/></Tabs>` 처럼 사용한다.
- 효과: props 폭발(prop drilling)을 막고 선언적이며 유연한 API를 제공한다.

### Slot Props (구 Render Props 대체)
**언제:** 한 컴포넌트에 영역이 여러 개(헤더/푸터/액션)인 레이아웃성 컴포넌트.
- `header`, `footer`, `actions` 같은 `ReactNode` prop으로 받는다.
- Render props(`children: (state) => ReactNode`)는 거의 쓰지 않는다 — 상태 공유가 필요하면 Compound Component, 단순 영역 분리면 Slot Props로 충분.

### children 합성
**언제:** 래퍼·레이아웃 컴포넌트.
- `children`만 받아 감싸는 컴포넌트. Props Drilling 해결의 1순위 도구.
- 가능하면 `<Layout><Sidebar /><Main /></Layout>`처럼 사용처에서 조립.

### Higher-Order Component (HOC)
- **신규 작성 금지가 기본** — Custom Hook과 합성으로 거의 모든 케이스를 해결한다.
- 기존 라이브러리 호환(`forwardRef` 같이 외부 API가 HOC를 요구할 때)에만 허용.

### Controlled / Uncontrolled Component
**언제:** 폼 요소를 만들 때.
- **Controlled**: 상태를 부모가 소유하고 검증·동기화가 필요할 때 (폼 라이브러리 없이 직접 만들 때의 기본).
- **Uncontrolled**: 단순 입력이고 제출 시점에만 값이 필요할 때 `ref`로 처리.
- **검증이 있는 폼은 react-hook-form**(`register` — uncontrolled 기반)을 쓴다 (`zod-usage` 스킬). shadcn Select·Checkbox 처럼 `ref` 를 받지 않는 부품만 `Controller` 로 감싼다.

### Extract Component (하위 컴포넌트 추출)
**언제:** JSX가 길거나 반복되는 마크업이 보일 때, 같이 실행되지 않는 분기가 한 컴포넌트에 묶여 있을 때.
- 반복되는 `map` 내부의 아이템 마크업은 별도 컴포넌트로 추출한다.
- **상호 배타적 분기**(예: viewer vs admin)는 부모에 분기점만 남기고 케이스별 자식 컴포넌트로 분할 — 한 파일 안에서 읽어야 할 맥락을 줄인다.
- 이름을 붙여 추출하면 의도가 드러나 가독성이 올라간다.

### Wrapper / Guard 컴포넌트 (구현 상세 추상화)
**언제:** 권한 체크, 인증 가드, 로깅 같은 횡단 관심사.
- `<AuthGuard><Page /></AuthGuard>` 식으로 가드 컴포넌트가 분기·리다이렉트를 흡수.
- 페이지 컴포넌트는 "정상 케이스"만 다루게 된다 — 한 컴포넌트가 처리할 개념 수 감소.

### Error Boundary / QueryBoundary
**언제:** 비동기 데이터·에러를 표시 컴포넌트 바깥에서 흡수하고 싶을 때.
- 표시 컴포넌트는 `data`가 확정된 상태만 그린다 — `isPending`/`isError` prop을 받지 않는다.
- 데이터 로딩은 `QueryBoundary`(`@/components/layout/QueryBoundary`), 예기치 못한 렌더 에러는 Next.js 에러 경계가 받는다 — 현재 `app/**/error.tsx` 도 별도 `ErrorBoundary` 도 없어 Next 기본 화면이 뜬다. 사용자용 에러 화면이 필요해지면 `app/error.tsx` 를 만든다.
- `Suspense`(suspense 모드 쿼리)는 쓰지 않는다 (`hooks-layer.md` 핵심 원칙 6). 자세한 사용은 `hooks-layer.md` 「UI 소비 — QueryBoundary」 참조.

---

## 작성 체크리스트

컴포넌트를 완성하기 전 스스로 확인한다.

- [ ] 컴포넌트가 `<PascalCase>/index.tsx` 폴더 구조이고, 위치(ui·layout·shared·도메인 components)가 맞는가?
- [ ] `app/**/page.tsx` 는 `features/*/pages` 의 `<X>Page` 를 import·export 만 하는가?
- [ ] 서버 데이터는 도메인 `hooks/` 로만 접근하는가? (services·axios 직접 호출 없음)
- [ ] 이 컴포넌트의 책임을 한 문장으로 말할 수 있는가?
- [ ] 데이터 페칭/로직과 렌더링이 섞여 있지 않은가? (섞였다면 hook으로 분리)
- [ ] 반복되거나 중첩이 깊은 JSX를 하위 컴포넌트로 추출했는가?
- [ ] 명령형 조작 대신 상태와 props로 선언적으로 표현했는가?
- [ ] 파생값을 `useState` + `useEffect`로 동기화하지 않았는가? (렌더 중 계산)
- [ ] Effect가 정말 "외부 시스템 동기화"인가? (이벤트 핸들러로 충분하지 않은지 확인)
- [ ] 컴포넌트가 너무 길지 않은가? 책임이 한 문장으로 떨어지는가?
- [ ] props 타입이 명확한가? (TS 인터페이스, `any` 금지)
- [ ] 핸들러/콜백 네이밍 규칙(`handleXxx` / `onXxx`)을 지켰는가?
- [ ] 같은 류 함수의 반환 타입이 통일돼 있는가?
- [ ] 매직 넘버/문자열을 상수로 빼냈는가?
- [ ] 리스트 `key`가 안정적 ID인가? (index 아님)
- [ ] `'use client'`가 필요한 잎(leaf)에서만 선언됐는가?
- [ ] 접근성: 시맨틱 태그, label 연결, alt 텍스트 확인?

---

## 안티패턴 (피해야 할 것)

- 하나의 컴포넌트가 페칭·상태·복잡한 렌더링을 모두 담당하는 "God Component".
- 깊게 중첩된 삼항 연산자로 조건부 UI를 표현하는 것.
- `useEffect`로 props ↔ state를 동기화하거나 파생값을 만드는 것 (렌더 중 계산으로 대체).
- `useEffect` 안에서 여러 관심사를 한꺼번에 처리하는 것 (1 effect = 1 동기화).
- prop drilling이 3단계 이상 이어지는 것 (① 합성 → ② Context 순서).
- 의미 없는 `div` 래퍼 남발 (Fragment 활용).
- 컴포넌트 내부에서 매 렌더마다 새 객체/함수를 자식에 무심코 내려보내는 것.
- **컴포넌트 안에 또 다른 컴포넌트를 정의하는 것** — 매 렌더마다 새 타입이 생겨 state·focus가 손실된다. 컴포넌트는 모듈 최상위에서 선언.
- 리스트 `key`에 `index` 사용 — 재정렬·삽입 시 잘못된 컴포넌트가 매칭된다.
- 함수 시그니처에 없는 부수효과(로깅·분석 이벤트·전역 변경)를 안에서 수행하는 것.
- 같은 이름의 함수가 다른 동작을 하는 것 (`http.get`이 토큰을 자동 첨부 등) — 이름을 바꾼다.
- 측정 없이 `memo`/`useMemo`/`useCallback`을 남발하는 것.
- 표시 컴포넌트에 `isLoading`/`isError` prop을 직접 받게 하는 것 — `QueryBoundary`로 흡수.
- DRY를 무기로 갈라질 가능성 있는 hook을 무리하게 통합하는 것 (중복 허용이 낫다).
- `app/**/page.tsx` 에서 화면을 직접 조합하거나 훅을 호출하는 것 — 도메인 `pages/<X>Page.tsx` 로.
- 공용 `components/shared`·`ui`·`layout` 에서 `features/` 를 import 하는 것 — props·config 주입으로.
- 컴포넌트를 폴더 없이 `components/{X}.tsx` 로 두는 것 — `components/{X}/index.tsx` (`ui/`·`layout/` 예외 제외).
