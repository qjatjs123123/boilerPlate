---
description: 프론트엔드 전체 아키텍처 지도 — frontend/ 아래 파일을 만들거나 수정하기 전에 먼저 읽는다
paths:
  - "frontend/**"
---

# Frontend Architecture — 전체 지도

프론트엔드 구조의 **단일 출처**. 폴더가 무엇을 맡고, 무엇이 무엇을 import 할 수 있는지를 정한다.
계층별 코드 작성법은 아래 「계층별 상세 규칙」 표의 rules 파일을 따른다.
프론트 구조·컨벤션의 **실행 기준은 `.claude/rules/frontend/`** 다. `docs/frontend/Convention.md` 는 사내 FE 컨벤션 **원문(참고용)** 이며, 이 프로젝트에 맞게 조정된 부분은 rules 가 우선한다 (차이 목록은 그 문서 상단). 버전·패키지는 `frontend/package.json` 기준. 규칙이 바뀌면 해당 rules 파일을 고친다.

> **경로 기준**: 소스는 `frontend/src/` 아래에 있다 (사내 컨벤션). 이 문서와 `.claude/rules/frontend/*.md` 에 적힌 `app/`·`components/`·`features/`·`lib/` 경로는 모두 `frontend/src/` 기준이다. `e2e/`·`swagger/`·`public/`·설정 파일만 `frontend/` 바로 아래. `@/` alias = `frontend/src/`.
>
> **우선순위**: 이 프로젝트의 `.claude/rules/frontend/*.md` 가 전역 `~/.claude/rules/frontend/*.md` 와 다르면 **프로젝트 규칙이 우선**한다 (사내 FE 컨벤션·아키텍처 반영본).

---

## 1. 사내 3계층

| 계층 | 위치 | 책임 |
|---|---|---|
| **Page Layer** | `src/app/` (Next.js App Router) | 라우팅만. `features/<도메인>/pages/<X>Page` 를 import 해서 `export default` (+ `metadata`). 레이아웃은 `app/layout.tsx` (`ReactQueryProvider` + `AppShell`) |
| **Feature Layer** | `src/features/<도메인>/` | 도메인 전용 pages·components·models·services·queries·hooks·store·utils·lib·constants·types |
| **Shared Layer** | `src/components/{ui,layout,shared}` (+ 반입 시 `DesignKit`), `src/{models,hooks,services,store,queries,utils,lib,constants,types}` | 공용. **특정 도메인(`features/`) import 금지** |

> 사내 문서(Vite + React Router 기준)의 `src/pages/` 는 App Router 의 `src/app/` 에 대응한다. **`src/pages/` 폴더는 만들지 않는다** — Next.js 가 Pages Router 로 인식해 충돌한다. `route.tsx` 는 불필요(폴더 구조가 곧 주소), `App.tsx` 역할은 `app/layout.tsx`.

```
브라우저 ─▶ app/{경로}/page.tsx ─▶ features/{domain}/pages/{Domain}Page ─▶ components/{Domain}Section
              (라우팅만)                   (도메인 화면)                             │
                                                                                    ▼
            backend ◀─ lib/axios ◀─ services/{domain}Service ◀─ queries/{domain}Queries ◀─ hooks/useRead{Domain}Page
            (FastAPI)              (safeParse + {Domain}Mapper)  (queryKey + queryFn)       (useQuery / useMutation)
```

- **기능 하나 = `features/{domain}/` 폴더 하나** — 백엔드 `app/domains/{domain}/` 과 1:1 짝.
- **서버 계약**: 백엔드 응답은 항상 `{status, data}` envelope. 프론트는 `swagger/docs.md` (sync-api-docs 가 생성, 수기 수정 금지) 기준으로 Zod 스키마를 만든다. 서버도 같은 요청에서 새로 만드는 중이면(vibe-build 병렬 개발) 짝 서버 spec 의 「API 설계」가 계약이고, 합친 뒤 swagger 와 대조한다.
- **새 기능**: 아래 표의 폴더 구성과 계층별 rules 의 템플릿을 따른다.

### Page Layer 예시 (`app/{경로}/page.tsx`)
```tsx
// 페이지 계층 — 라우팅만 담당. 화면은 features/{domain}/pages/{Domain}Page
import { PostPage } from '@/features/post/pages/PostPage';

export const metadata = { title: '게시글' };

export default PostPage;
```

---

## 2. Feature Layer — `features/{domain}/`

| 폴더 | 역할 | 파일 예 | 상세 규칙 |
|---|---|---|---|
| `pages/` | 도메인 페이지 화면 `<X>Page.tsx` (named export) | `pages/{Domain}Page.tsx` | 이 문서 |
| `components/<Name>/index.tsx` | 도메인 전용 컴포넌트 (폴더 = PascalCase 컴포넌트명, 전용 hooks·config·`__tests__` 를 같은 폴더에) | `components/{Domain}Section/index.tsx`, `{domain}{Name}Config.ts` | `react-convention.md` |
| `models/` | ACL·Adapter: Zod 스키마(서버 DTO) + Mapper | `models/{domain}Schema.ts`, `models/{domain}Mapper.ts` (`{Domain}Mapper`) | `models-layer.md` |
| `services/` | API 호출 + safeParse + Mapper + 비즈니스 로직. `class {Domain}Service` + 싱글턴 `{domain}Service` | `services/{domain}Service.ts` | `services-layer.md` |
| `queries/` | queryKey factory + queryOptions | `queries/{domain}QueryKeys.ts`, `queries/{domain}Queries.ts` (`{domain}PageQuery`) | `queries-layer.md` |
| `store/` | 도메인 전역 클라이언트 상태 (Zustand, 필요 시 설치) | — | `store-layer.md` |
| `hooks/` | 읽기 `useRead*`(useQuery) / 쓰기 `useCreate·Update·Delete*`(useMutation) | `hooks/useRead{Domain}Page.ts`, `hooks/useDelete{Domain}.ts` | `hooks-layer.md` |
| `constants/` | 상수 (UPPER_SNAKE_CASE) | `constants/{domain}Constants.ts` | `types-layer.md` |
| `types/` | 화면 모델 타입 (`I`/`T` 접두사), `{name}Type.ts` | `types/{domain}Type.ts` | `types-layer.md` |
| `utils/`, `lib/` | 도메인 전용 순수 유틸 / 외부 라이브러리 래퍼 | — | 이 문서 |

- **폴더는 필요할 때만** 만든다 (빈 폴더 금지). 테스트는 대상 옆 `__tests__/`.
- **models vs services**: `models` 는 서버 응답의 **모양**(Zod 스키마 + Mapper, 네트워크 없음), `services` 는 **행동**(실제 호출 + models 로 검사·변환 + 비즈니스 로직).

### 새 기능 하나가 거치는 파일 (만드는 순서)

```
features/{기능}/types/{기능}Type.ts                 화면용 타입 (I/T 접두사, camelCase)
features/{기능}/constants/{기능}Constants.ts        상수 (필요할 때만)
features/{기능}/models/{기능}Schema.ts              응답 DTO Zod 스키마 (swagger/docs.md 또는 짝 서버 spec 「API 설계」 기준)
features/{기능}/models/{기능}Mapper.ts              DTO → 화면 모델 변환
features/{기능}/services/{기능}Service.ts           API 호출 + safeParse + Mapper
features/{기능}/queries/{기능}QueryKeys.ts          queryKey 단일 출처
features/{기능}/queries/{기능}Queries.ts            queryOptions (queryKey + queryFn)
features/{기능}/hooks/useRead{Domain}*.ts           읽기 훅
features/{기능}/hooks/use{Create|Update|Delete}{Domain}.ts   쓰기 훅 (성공 시 목록 키 invalidate)
features/{기능}/components/{Name}/index.tsx         화면 부품
features/{기능}/pages/{Name}Page.tsx                페이지 화면
features/{기능}/**/__tests__/*.test.ts(x)           Vitest + MSW
app/{경로}/page.tsx                                 import 후 export default (+ metadata)
components/layout/AppShell.tsx                      NAV_ITEMS 에 메뉴 추가 (공유 파일 — vibe-build 병렬 개발에선 화면-기반/데이터 묶음 맨 앞 Task, COMMON.md §5)
e2e/{기능}.spec.ts (frontend/ 바로 아래)              핵심 흐름 Playwright
```

### 도메인 내부 의존 방향 (ESLint 강제)

```
types · constants · utils · lib  →  models  →  services  →  queries  →  store  →  hooks  →  components  →  pages
```

**오른쪽(위) 계층은 왼쪽(아래) 계층을 import 할 수 있고, 반대는 금지.** 이 순서의 단일 출처는 이 문서다 (다른 rules 는 여기를 참조).

> **store 예외**: `store/` 는 순서상 queries 위에 있지만 `types`·`constants`·`utils`·`lib` **만** import 한다 (`models`·`services`·`queries` 금지 — 서버 데이터를 모르는 순수 클라이언트 상태, `store-layer.md`).

예:
- `components/` → `hooks/`·`queries/`·`types/`·`constants/` ✅ / `services/` 직접 import **금지** — 서버 데이터는 반드시 `hooks/` 경유 (ESLint 미강제, 관례로 금지).
- `hooks/` → `queries/`·`services/`·`store/` ✅ / `components/` ❌.
- `services/` → `models/`·`types/` ✅ / `queries/`·`hooks/` ❌.
- `models/` → `types/` ✅ / `services/` ❌.

### 에러 흐름

| 발생 위치 | 에러 (`@/utils/errors`) | 의미 |
|---|---|---|
| services (HTTP 실패) | `DataLayerError` | 네트워크·서버 문제 |
| services (safeParse 실패) | `DomainLayerError` (`throwDomainError`) | 백엔드 응답 형식 변경 의심 |
| components/hooks | 일반 에러 | 프론트 코드 버그 |

화면 표시는 `components/layout/QueryBoundary` (로딩·에러 경계) + toast (`error-toast` 스킬).

---

## 3. Shared Layer

> **초기 상태**: 템플릿은 Next.js 설치 직후 상태라 아래 공용 파일(`components/ui`·`components/layout`·`lib/*`·`utils/*`)이 아직 없다. 첫 기능을 만들 때 이 표와 각 rules 의 템플릿대로 생성하고, `app/layout.tsx` 를 `ReactQueryProvider` + `AppShell` 로 감싼다. shadcn 부품은 `pnpm dlx shadcn@latest init` 후 `add <부품>`.

| 경로 | 내용 | 규칙 |
|---|---|---|
| `components/ui/` | **shadcn/ui 순수 UI** (button, table, checkbox …) — CLI 생성 파일명·코드 유지. 추가는 `pnpm dlx shadcn@latest add <부품>` | `react-convention.md` |
| `components/layout/` | 앱 골격: `AppShell.tsx`(메뉴 `NAV_ITEMS`), `QueryBoundary.tsx`(로딩/에러/빈 상태 경계) | `react-convention.md` |
| `components/shared/<Name>/index.tsx` | 도메인을 넘나드는 재사용 컴포넌트 (ui 부품 조합 + 동작). 예: 게시판형 목록이라면 `components/shared/{Name}/` (index.tsx = 본체, `BoardTable.tsx` 등 하위 부품, `{name}Type.ts` — 두 도메인 이상이 쓸 때 만든다). 데이터는 **props·config 주입**으로만 받는다 | `react-convention.md` |
| `lib/` | `axios.ts`(axiosInstance 단일 진입점), `ReactQueryProvider.tsx`(전역 쿼리 정책), `toast.ts`(화면 알림 단일 진입점 — 디자인 킷 연결 지점), `currentUser.ts`(개발용 현재 사용자 id), `utils.ts`(shadcn `cn`) | `axios.md`, `error-toast` 스킬 |
| `utils/` | `errors.ts`(DataLayerError·DomainLayerError·throwDomainError·toUserMessage), `formatDate.ts`(`formatDateDot`) — 도메인 무관 순수 함수 | `javascript-convention.md` |
| `hooks/` | 공용 훅 / 여러 도메인 단순 조회 조합 (예: `useQnaAndFaq.ts`) — **공용 계층 중 유일하게 `features/*/queries/` 만 import 가능** | `hooks-layer.md` |
| `models/`·`services/`·`queries/`·`store/`·`constants/`·`types/` | 도메인 무관 공용 버전 (필요할 때만) | 각 레이어 rules |
| `components/DesignKit/` | **사내 디자인 킷(디자인 킷)** — 반입 시에만 존재. 외부 반입 코드라 `ui/` 와 같이 네이밍·구조 규칙의 예외, 수정 금지. 글꼴 파일도 여기서 가져온다 (`font.md`) | — |

**ui / layout / shared 구분**: `ui` = 동작 없는 원자 부품(shadcn), `layout` = 앱 뼈대·경계, `shared` = 여러 도메인이 config 를 주입해 쓰는 복합 컴포넌트. 한 도메인에서만 쓰면 shared 가 아니라 `features/<도메인>/components/`.

**공용 계층 내부 의존 방향**: 도메인과 같은 순서를 따른다 — `src/{types,constants,utils,lib} → src/models → src/services → src/queries → src/store → src/hooks → src/components`. 예: `src/services` 가 `src/hooks` 를, `src/hooks` 가 `src/components` 를 import 하지 않는다 (ESLint 강제).

메뉴 추가는 `components/layout/AppShell.tsx` 의 `NAV_ITEMS`. 그 외 루트: `e2e/` (Playwright — `./fixtures` 의 `test`/`expect` 사용), `swagger/docs.md` (API 계약, 생성물 — 수기 수정 금지).

---

## 4. 도메인 간 의존 (FEATURE_DEPENDENCIES)

- **도메인 간 직접 import 금지** — `features/qna` 가 `features/faq` 를 import 하면 ESLint 에러.
- **상위 도메인이 하위 도메인을 조합할 때만** `frontend/eslint.config.mjs` 의 `FEATURE_DEPENDENCIES` 에 **한 방향**으로 등록한다:
  ```js
  const FEATURE_DEPENDENCIES = { support: ["qna", "faq"] };   // support → qna·faq ✅, qna → support ❌
  ```
  상위 도메인은 하위 도메인의 `queries/`(queryOptions·queryKeys) **만** 가져다 조합한다 (ESLint 강제). 역방향은 절대 등록하지 않는다 (순환 방지).
- **단순 조회 조합**(화면 하나에 두 도메인 목록을 나란히)은 상위 도메인을 만들지 말고 공용 `src/hooks/useQnaAndFaq.ts` 같은 훅으로. 이 훅은 각 도메인의 `queries/`(queryOptions) **만** import 한다 (services·hooks·components 등 금지 — ESLint 강제).
- 조합이 **새 비즈니스 개념**(예: 고객지원 = QnA + FAQ 통합 관리)으로 커지면 상위 도메인 `features/support/` 를 만들고 FEATURE_DEPENDENCIES 에 등록한다.
- 위 `src/hooks` 예외를 빼면, 공용 계층(`components/`·`utils/`·`services/` …)은 어떤 `features/` 도 import 하지 않는다.

---

## 5. 공통 원칙

- 배럴(`index.ts`) 금지 — 컴포넌트 폴더의 `index.tsx` 는 **컴포넌트 본체**이지 re-export 배럴이 아니다. import 는 폴더 경로로 (`@/components/shared/{Name}`, `../components/{Domain}Section`).
- 같은 도메인 안은 상대 경로(`../services/{domain}Service`), 공용·다른 계층 루트는 `@/` alias.
- SSR(사내 Q7 getServerSideProps) 대응: 도메인 `pages/{X}Page.tsx`(서버 컴포넌트)에서 queries 의 queryOptions 로 prefetch + `HydrationBoundary`. 데이터 로직은 도메인 services, 렌더링은 도메인 컴포넌트(데이터는 hooks 경유) — 상세는 `react-convention.md` 「Server vs Client Component 경계」.
- service 는 모듈 싱글턴 export, DI·인터페이스·Mock 클래스 없음. service 테스트는 MSW, hooks 테스트는 `vi.mock` 으로 service 싱글턴을 모킹 (`hooks-layer.md`).
- 테스트는 대상 파일 옆 `__tests__/` (Vitest), 화면 흐름은 `e2e/{기능}.spec.ts`.

---

## 6. 강제 방식 (`frontend/eslint.config.mjs`)

| 규칙 | 강제 수단 |
|---|---|
| 도메인 내부 의존 방향 (types → models → services → queries → store → hooks → components → pages) | `import/no-restricted-paths` (FEATURE_LAYERS) |
| 도메인 간 직접 import 금지 / FEATURE_DEPENDENCIES 한 방향 허용 | 같음 (featureZones) |
| 공용 계층 → `features/` 금지 (예외: `src/hooks` → `features/*/queries` 만 허용) | 같음 |
| 공용 계층 내부 의존 방향 (`src/types…` → … → `src/components`) | 같음 (SHARED_LAYERS) |
| `store/` 는 `types`·`constants`·`utils`·`lib` 만 (models·services·queries 금지) | 같음 (storeZones) |
| `app/` 은 `features/` 중 `pages/` 만 import (공용 lib·components 는 허용 — `layout.tsx`) | 같음 |
| `lib/axios` 는 `services/` (도메인·공용) 에서만, `axios` 패키지는 `lib/axios.ts`·services 에서만 | `import/no-restricted-paths` + `no-restricted-imports` |
| components 가 서버 데이터를 hooks 경유로만 사용 (services 직접 import 금지) | **관례** — 리뷰·`frontend/refactor` 스킬에서 확인 |

ESLint 는 `make check`, Stop 품질 게이트, CI 에서 실행된다. 위반 시 에러 메시지의 rules 파일을 읽고 의존을 올바른 계층으로 옮긴다 — 규칙을 끄지 않는다.

---

## 7. 계층별 상세 규칙

| 대상 | 파일 |
|---|---|
| types/, constants/ | `.claude/rules/frontend/types-layer.md` |
| models/ | `.claude/rules/frontend/models-layer.md` |
| services/ | `.claude/rules/frontend/services-layer.md` |
| lib/axios.ts | `.claude/rules/frontend/axios.md` |
| queries/ | `.claude/rules/frontend/queries-layer.md` |
| store/ | `.claude/rules/frontend/store-layer.md` |
| hooks/ | `.claude/rules/frontend/hooks-layer.md` |
| components/, pages/, React 전반 | `.claude/rules/frontend/react-convention.md` |
| 네이밍 / 함수 | `naming-convention.md` / `javascript-convention.md` |
| 글꼴 (`app/layout.tsx`, `app/globals.css`) | `.claude/rules/frontend/font.md` |
| 화면 규칙 (4상태·한국어·Tailwind·44px·아이콘) | `.claude/rules/frontend/react-convention.md` 「화면 규칙」 |
| Git·커밋·PR | `docs/CONVENTIONS.md` 「Git」 (프론트·백엔드 공통) |
