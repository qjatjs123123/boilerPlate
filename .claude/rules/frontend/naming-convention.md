---
description: 변수·함수·타입·React 이름 짓기 규칙 — 모든 JS/TS 코드 작성 시
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---

# 네이밍 컨벤션 (변수·함수·타입·React)

변수·함수·타입 이름 짓기 규칙. 코드를 작성·수정하기 전에 읽고 따른다.
포매터가 처리하는 영역(따옴표, 들여쓰기)은 다루지 않는다.

> **이 프로젝트 전용 (사내 FE 컨벤션 반영)** — 전역 `~/.claude/rules/frontend/naming-convention.md` 와 다르면 **이 파일이 우선**한다. 특히 타입 이름은 `I`/`T` 접두사(아래 「타입」)다.
> 아래 표의 도메인 이름 예시(`post`, `IPost` …)는 **가상의 게시글 기능** 기준이다 (실제 파일 없음).
> 폴더 구조·계층별 파일명은 `architecture.md` 와 각 레이어 rules(`types-layer.md`·`models-layer.md`·`services-layer.md` 등)를 따른다.
> **예외 — `src/components/ui/`(shadcn/ui CLI 생성 코드)** 는 이 규칙을 적용하지 않고 원본 그대로 둔다 (kebab 파일명, `React.ComponentProps`, 접두사 없는 타입). 새 부품은 `pnpm dlx shadcn@latest add <부품>` 으로만 추가.

## 폴더·파일

| 대상 | 규칙 | 예시 |
|---|---|---|
| 폴더 (도메인·계층) | kebab-case — 규칙 문서의 `features/{domain}/` 도 폴더명은 kebab-case 로 읽는다. 그 안의 파일명·코드에선 camelCase (`features/blog-post/services/blogPostService.ts`) | `features/blog-post/`, `features/post/services/` |
| **컴포넌트 폴더** | PascalCase 컴포넌트명, 본체는 `index.tsx` | `components/PostListSection/index.tsx`, `components/shared/{Name}/index.tsx` |
| 컴포넌트 파일 (폴더 안 하위 부품·페이지) | PascalCase | `BoardTable.tsx`, `pages/PostPage.tsx` |
| 훅·유틸·service 등 그 외 파일 | camelCase | `useReadPostPage.ts`, `postService.ts`, `formatDate.ts` |
| 타입 전용 파일 | `{name}Type.ts` — `.d.ts` 쓰지 않는다 (`skipLibCheck` 로 오류가 검사되지 않음) | `types/postType.ts`, `boardType.ts` |
| 상수 파일 | `{name}Constants.ts` | `constants/postConstants.ts` |
| 계층별 파일명 | 레이어 rules 그대로 | `models/postSchema.ts`, `models/postMapper.ts`, `services/postService.ts`, `queries/postQueryKeys.ts`, `queries/postQueries.ts` |
| shadcn 부품 | CLI 생성 kebab 파일명 유지 | `components/ui/button.tsx` |

### 계층별 export 이름

| 대상 | 이름 | 예시 |
|---|---|---|
| 페이지 화면 | `{X}Page` (named export) | `PostPage` |
| Zod 스키마 / 추론 타입 | `{Name}DtoSchema` / `T{Name}Dto` | `PostDtoSchema` / `TPostDto` |
| Mapper | `{Domain}Mapper` (class) | `PostMapper` |
| service | class `{Domain}Service` + 싱글턴 `{domain}Service` | `PostService`, `postService` |
| queryKey factory | `{domain}Keys` | `postKeys` |
| queryOptions | `{domain}{Target}Query` | `postPageQuery` |
| 읽기 / 쓰기 훅 | `useRead{Domain}*` / `useCreate·Update·Delete{Domain}`, `use{Action}{Domain}` | `useReadPostPage`, `useBulkDeletePost` |
| store | `use{Domain}{Target}Store` | `usePostFilterStore` |

---

## 변수

| 규칙 | 예시 |
|---|---|
| 변수·함수는 camelCase | `const helloWorld = () => {}` |
| 배열 변수는 `List` 접미사 | `const helloList = ['hello', 'world']` |
| boolean 변수는 `is`/`has`/`can` 접두사 | `const isLoading = false` |
| 클래스·생성자는 PascalCase | `class Hello {}` |
| 상수는 UPPER_SNAKE_CASE | `const HELLO_WORLD = 'helloWorld'` |
| 상수 모음 객체: 이름은 UPPER, 키는 camelCase | `const HELLO = { hiWorld: 'hiWorld' }` |
| Enum: 이름 UPPER, 멤버 PascalCase | `enum HI { HelloWorld = 1 }` |

## 함수 — 동사 접두사

함수 이름은 **동사 접두사 + 명사** 형태. 역할별 접두사:

| 접두사 | 역할 | 예시 |
|---|---|---|
| `is` / `has` / `can` | boolean 반환 판별 함수 | `isClient()` |
| `create` | 무언가를 생성 | `createHelloWorld()` |
| `convert` | 입력을 특정 형태로 변환 (배열 요소 변환 포함) | `convertHello()` |
| `get` | 입력에서 특정 값을 가져와 반환 | `getHello()` |
| `open` | 무언가를 여는 동작 | `openHello()` |
| `add` / `minus` | 더하기 / 빼기 | `addHello()`, `minusHello()` |
| `filter` | 배열을 필터링해 반환 | `filterHello(array)` |
| `find` | 배열에서 특정 요소를 찾아 반환 | `findHello(array)` |

- 관행적 유틸 함수는 관행을 따른다: `throttle`, `debounce`, `commaize`, `decommaize` 등.
- **`to{Target}` 예외** — 변환 대상이 이름의 핵심인 Mapper static 메서드(`toDomain`, `toSummary`, `toCreateDto`)와 에러 변환 헬퍼(`toDataLayerError`, `toUserMessage`)는 `to` 를 쓴다. 그 외 변환 함수는 `convert`.
- 위에 없는 경우도 되도록 동사 접두사 형태로: `parseHello()` 등.

## React

| 규칙 | 예시 |
|---|---|
| 커스텀 훅은 `use` 접두사 | `useCustomHook()` |
| 이벤트 핸들러는 `handle` 접두사 + 이벤트 유형 접미사 | `handleHiClick()` |
| props로 받는 콜백은 `onXxx` | `onSubmit`, `onClose` |
| Context는 `Context` 접미사 | `const HelloContext = createContext(null)` |
| Context 소비 훅은 `use~Context` | `useHelloContext()` |
| Provider 컴포넌트는 `Provider` 접미사 | `HelloContextProvider` |
| 모든 Provider를 래핑하는 최상위는 `Providers` | `<Providers>{children}</Providers>` |
| HOC는 `with` 접두사 | `withAuth()` — 단, 신규 HOC 작성은 기본 금지(`react-convention.md`), 기존 라이브러리 호환 시에만 |

## 타입 — `I` / `T` 접두사 (사내 컨벤션)

| 선언 | 접두사 | 예시 |
|---|---|---|
| `interface` | `I` | `interface IBoardTableProps {}`, `interface IPost {}` |
| `type` 별칭 | `T` | `type TPostDto = z.infer<...>`, `type TRequestKind = 'json' \| 'form'` |

- **도메인 모델·DTO 도 예외 없음**: `IPost`, `IPostPage`, `ICreatePostInput`, `TPostDto`, `TPostListResponseDto`.
- **Props 는 접두사 + `Props` 접미사**: `IBoardTableProps`, `TButtonProps`.
- **`Type` 접미사는 붙이지 않는다** (접두사가 타입임을 이미 표시): `IBoardColumn` (❌ `BoardColumnType`).
- 객체 형태는 `interface` 를 기본으로, 유니온·교차·`z.infer`·매핑 타입은 `type`.
- **값과 이름이 겹치지 않는다**: Zod 스키마 상수는 `PostDtoSchema`, 그 추론 타입은 `TPostDto`. Mapper 클래스 `PostMapper` 는 값이므로 접두사 없음.
- **제네릭 매개변수**는 `T` 또는 `TRow`·`TData` 처럼 `T` + 의미 (기존 관행 유지).
- **유틸리티 타입**도 `T` 접두사: `TOmitFromPick<T, U>`.
- **외부 라이브러리 타입은 그대로**: `UseQueryResult`, `ReactNode`.
- **React 타입은 개별 import**: `ReactNode` (❌ `React.ReactNode`).
- **API 요청·응답 타입(`TPostDto` 등)은 Mapper 로 변환된 뒤 상위 계층에 남기지 않는다** — DTO 는 `models/`·`services/` 안에서만 쓴다. 화면 모델은 `types/{domain}Type.ts`.
- 컴포넌트 타입은 같은 파일 상단에 두는 것을 기본으로, 여러 파일이 공유하면 `{name}Type.ts` 로 분리한다.

## 한글 이름

- 원칙은 영어. **영어로 의미를 담기 어려운 상수·함수에 한해** 한글 허용 (예: 법령·회계 용어 상수).
- 화면 문구는 이름이 아니라 값(문자열)으로 둔다.

---

## 체크리스트

- [ ] 배열 변수에 `List` 접미사?
- [ ] boolean 변수·판별 함수가 `is`/`has`/`can`으로 시작?
- [ ] 함수가 역할에 맞는 동사 접두사(`create`/`convert`/`get`/`filter`/`find` 등)를 가지는가?
- [ ] 핸들러 `handleXxx(이벤트유형)` / prop 콜백 `onXxx`?
- [ ] Context 관련 이름(`~Context`, `use~Context`, `~Provider`) 규칙 준수?
- [ ] `interface` 는 `I`, `type` 은 `T` 접두사? (도메인 모델·DTO 포함, `Type` 접미사 없음, Props 는 `~Props`)
- [ ] 폴더 kebab-case(컴포넌트 폴더만 PascalCase + `index.tsx`), 컴포넌트 파일 PascalCase, 타입 파일 `{name}Type.ts`(`.d.ts` 아님), 상수 파일 `{name}Constants.ts`?
- [ ] 계층별 export 이름(`{Domain}Mapper`, `{domain}Service`, `{domain}Keys`, `{domain}{Target}Query`, `useRead*`) 준수?
- [ ] `React.ReactNode` 같은 네임스페이스 접근 없이 개별 import?
