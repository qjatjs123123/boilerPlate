# CLAUDE.md — Frontend

Next.js 16 App Router 기반 UI 레이어 **프로젝트 템플릿**.
소스는 `frontend/src/` 아래 (이 문서의 `app/`·`components/`·`features/`·`lib/`·`utils/` 경로는 모두 `src/` 기준). 코딩 규칙(사내 FE 컨벤션 반영)은 `../.claude/rules/frontend/` 가 우선한다.
**사내 FE 3계층 아키텍처 (Page · Feature · Shared)**.

본 문서는 특정 도메인(post, user 등)에 종속되지 않은 **재사용 가능한 가이드**이다.
실제 도메인 명은 `{domain}` 자리에 들어간다.

---

## 기술 스택

| 항목 | 기술 |
|---|---|
| Framework | Next.js 16 (App Router, RSC) — 학습 데이터와 API가 다를 수 있으니 `AGENTS.md` 참고 |
| Language | TypeScript 5+ |
| Styling | Tailwind CSS v4 |
| UI 라이브러리 | shadcn/ui (Radix) — `src/components/ui/`, 추가는 `pnpm dlx shadcn@latest add <부품>` |
| State | TanStack Query v5 (클라이언트 상태가 필요해지면 Zustand 를 `pnpm add zustand` 로 추가) |
| Validation | Zod |
| HTTP Client | axios |
| Test | Vitest + MSW + Playwright |

> Markdown 등 도메인 특화 라이브러리는 프로젝트별 README에 별도 명시.

---

## 아키텍처 개요 — 사내 3계층

| 계층 | 위치 (`src/` 기준) | 책임 |
|---|---|---|
| **Page Layer** | `app/` | 라우팅만. `features/{domain}/pages/{X}Page` 를 import 해 `export default` (+ `metadata`). 레이아웃은 `app/layout.tsx` (사내 `App.tsx` 역할 — ReactQueryProvider + AppShell) |
| **Feature Layer** | `features/{domain}/` | 도메인 전용 pages·components·models·services·queries·hooks·store·utils·lib·constants·types |
| **Shared Layer** | `components/{ui,layout,shared}/`, `{models,hooks,services,store,queries,utils,lib,constants,types}/` | 공용. 특정 도메인(`features/`) import 금지 (예외: `hooks/` 는 단순 조회 조합용으로 `features/*/queries/` 만 가능) |

> 사내 문서의 `src/pages/` = 이 프로젝트의 `src/app/`. `src/pages/` 는 Next.js Pages Router 로 인식돼 충돌하므로 만들지 않는다.

### 의존성 방향 (도메인 내부, 단방향)
```
types · constants · utils · lib → models → services → queries → store → hooks → components → pages
```
- 아래 계층은 위 계층을 import 할 수 없다 — `eslint.config.mjs` 의 `import/no-restricted-paths` 로 강제. 위반 시 에러 메시지에 읽을 rules 파일이 적혀 있다.
- `app/` 은 `features/*/pages` 만 import.
- 공용 계층은 `features/` import 금지 — 예외: 공용 `hooks/` 는 `features/*/queries/` 만 import 가능 (`architecture.md` 「도메인 간 의존」).
- `axios` 패키지·`@/lib/axios` 는 `lib/axios.ts` 와 `services/`(도메인·공용) 에서만 import 가능 (ESLint 강제).
- 도메인 간 직접 import 금지. 상위 도메인이 하위 도메인을 조합할 때만 `eslint.config.mjs` 의 `FEATURE_DEPENDENCIES` 에 한 방향 등록 (예: `{ support: ["qna", "faq"] }`). 단순 조회 조합은 공용 `src/hooks/`.

### Service 인스턴스화 (DI 없음)

Service 는 **클래스 + 모듈 레벨 싱글톤**으로 export 한다.
- 인터페이스 분리·DI 컨테이너 없음. 테스트에서는 MSW 로 HTTP 를 가로채므로 Mock 구현체도 불필요.

```ts
// features/{domain}/services/{domain}Service.ts
import { axiosInstance } from '@/lib/axios';

export class {Domain}Service { /* axiosInstance 호출 + safeParse + Mapper */ }
export const {domain}Service = new {Domain}Service();
```

`queries/` 의 queryFn 과 `hooks/` 의 mutationFn 이 위 싱글톤을 import 하여 사용한다.

---

## 디렉토리 구조 (템플릿)

> **초기 상태**: 클론 직후 `src/` 에는 Next.js 설치 직후의 `app/`(layout·page·globals.css·favicon)만 있다. 아래의 `components/`·`lib/`·`utils/`·`features/` 와 layout 의 ReactQueryProvider·AppShell 은 **첫 기능을 만들 때** 이 구조대로 생성한다.

```
frontend/
├── src/                            # 소스 루트 (사내 컨벤션) — `@/` alias = src/
│   ├── app/                        # Page Layer — 라우팅만
│   │   ├── layout.tsx              # ReactQueryProvider + AppShell (사내 App.tsx 역할)
│   │   ├── page.tsx                # → features/home/pages/HomePage
│   │   ├── globals.css
│   │   └── {경로}/page.tsx         # import {X}Page → export default (+ metadata)
│   │
│   ├── features/                   # Feature Layer — 도메인별 모듈
│   │   └── {domain}/
│   │       ├── pages/              # {X}Page.tsx — 페이지 화면
│   │       ├── components/         # {Name}/index.tsx (+ 전용 config·hooks·__tests__)
│   │       ├── models/             # {domain}Schema.ts (Zod DTO), {domain}Mapper.ts ({Domain}Mapper)
│   │       ├── services/           # {domain}Service.ts ({Domain}Service + {domain}Service)
│   │       ├── queries/            # {domain}QueryKeys.ts, {domain}Queries.ts (queryOptions)
│   │       ├── hooks/              # useRead{Domain}*.ts (useQuery), use{Create|Update|Delete}{Domain}.ts (useMutation)
│   │       ├── store/              # Zustand 도메인 상태 (필요 시)
│   │       ├── constants/          # {domain}Constants.ts (UPPER_SNAKE_CASE)
│   │       ├── types/              # {domain}Type.ts (I/T 접두사)
│   │       └── utils/ · lib/       # 도메인 전용 유틸 / 외부 라이브러리 래퍼
│   │
│   ├── components/                 # Shared — 공용 UI (도메인 무관)
│   │   ├── ui/                     # shadcn/ui 부품 (CLI 생성 — alert-dialog, button, checkbox, input, label, select, skeleton, table, textarea)
│   │   ├── layout/                 # AppShell.tsx (NAV_ITEMS), QueryBoundary.tsx
│   │   └── shared/                 # 도메인을 넘나드는 재사용 컴포넌트 — {Name}/ (index.tsx, 하위 부품, {name}Type.ts) · 필요할 때만
│   │
│   ├── lib/                        # axios.ts (axiosInstance 단일 진입점), ReactQueryProvider.tsx, toast.ts (화면 알림 단일 진입점), currentUser.ts, utils.ts (cn)
│   ├── utils/                      # errors.ts (DataLayerError·DomainLayerError·throwDomainError), formatDate.ts (formatDateDot)
│   └── hooks/ · services/ · store/ · queries/ · models/ · constants/ · types/   # 공용 — 필요할 때만 생성
│
├── e2e/                            # Playwright
├── swagger/docs.md                 # API 계약 (자동 생성)
└── public/                         # Next.js 정적 파일
```

### 폴더 규칙

- **폴더는 필요할 때만** — 빈 폴더 금지.
- **컴포넌트는 폴더 단위** — `components/{Name}/index.tsx` (폴더 = PascalCase 컴포넌트명). 전용 config·hooks·`__tests__` 는 같은 폴더에.
- **배럴(`index.ts`) 사용 금지** — 항상 직접 경로로 import (컴포넌트 `index.tsx` 는 배럴이 아니라 본체). 트리쉐이킹과 탐색성 모두 유리.
- **도메인 store vs 공용 store** — 도메인 상태는 `features/{domain}/store/`, 여러 도메인이 쓰는 UI 상태는 `src/store/`.
- **테스트는 대상 옆 `__tests__/`**.

---

## 계층별 역할 (도메인 폴더)

| 폴더 | 위치 | 책임 | 에러 타입 |
|---|---|---|---|
| **types / constants** | `features/{domain}/types/`, `constants/` | 화면 모델 타입(`I`/`T`), 상수 | — |
| **models** | `features/{domain}/models/` | Zod schema(DTO 묘사), DTO → 화면 모델 Mapper (ACL·Adapter) — 순수, 예외를 던지지 않음 | — |
| **services** | `features/{domain}/services/` | axios 호출 + safeParse + Mapper + 비즈니스 로직 | `DataLayerError` (네트워크/서버 문제), `DomainLayerError` (safeParse 실패 — BE 스키마 변경 의심) |
| **queries** | `features/{domain}/queries/` | queryKey + queryFn (`queryOptions`) 단일 출처 | 라이브러리 에러 |
| **store** | `features/{domain}/store/` | Zustand 도메인 상태 (draft, 필터, UI 토글 등) | 일반 런타임 에러 |
| **hooks** | `features/{domain}/hooks/` | 읽기 `useRead*`(useQuery) / 쓰기 `useCreate/Update/Delete*`(useMutation + invalidate) | 라이브러리 에러 |
| **components / pages** | `features/{domain}/components/`, `pages/` | UI, 화면 조합 | 프론트엔드 코드 버그 |

---

## 주요 설계 원칙

- **배럴 export 없음** — 직접 경로 import.
- **Service 는 모듈 싱글톤** — 인터페이스 분리, DI 컨테이너, Mock 클래스 모두 없음. 테스트는 MSW 로.
- **단방향 의존** — `import/no-restricted-paths` 로 강제.
- **axios → fetch 등 HTTP 클라이언트 교체**는 `lib/axios.ts` + 각 services 파일만 수정.
- **queryKey 단일 출처** — mutation 이 `queryClient.invalidateQueries(...)` 를 호출할 때 쓰는 queryKey 는 반드시 `queries/{domain}QueryKeys.ts` 에서 import.
- **SSR(사내 `getServerSideProps`)** — 도메인 `pages/{X}Page.tsx`(서버 컴포넌트)에서 queryOptions prefetch + `HydrationBoundary`. 상세는 `.claude/rules/frontend/react-convention.md` 「Server vs Client Component 경계」.

---

## 비기능 요구사항 (체크리스트, 프로젝트별 조정)

- **SEO**: `generateMetadata`, ISR (`revalidate`), `app/sitemap.ts`, `app/robots.ts`, JSON-LD
- **반응형**: Tailwind breakpoint, 버튼 최소 44×44px
- **성능**: `next/image`, dynamic import, bundle analyzer

---

## 개발 명령어

```bash
pnpm dev             # 개발 서버
pnpm build           # 프로덕션 빌드
pnpm lint            # 린트
pnpm type-check      # TypeScript 체크
pnpm test            # Vitest 단위/통합 테스트
pnpm test:e2e        # Playwright E2E (e2e/fixtures.ts 의 test 사용 — 콘솔 에러 자동 실패)
```

## 하네스 규칙 (이 템플릿 전용)

- 도메인 폴더: `features/{domain}/` (pages·components·models·services·queries·hooks·constants·types + 테스트) — 새 도메인은 `.claude/rules/frontend/*.md` 의 계층 규칙·템플릿을 따른다.
- 페이지: 화면은 `features/{domain}/pages/{X}Page.tsx`, `app/{경로}/page.tsx` 는 import 후 `export default` 만 (AppShell 은 `app/layout.tsx` 가 이미 감싼다). 메뉴는 `components/layout/AppShell.tsx` 의 `NAV_ITEMS` 에 추가한다.
- e2e: `e2e/{기능}.spec.ts` 는 `@playwright/test` 대신 `./fixtures` 의 `test`/`expect` 를 import 한다 (console error·pageerror 발생 시 자동 실패, `HARNESS_RUN_DIR` 지정 시 로그 기록).
- API 계약: `swagger/docs.md` 는 `backend/sync-api-docs` 스킬이 백엔드 코드에서 생성한다. 손으로 고치지 않는다.
