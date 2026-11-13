---
description: features/{domain}/types/·constants/ 또는 src/types/·src/constants/ 폴더 내 파일({name}Type.ts, {domain}Constants.ts) 작성 또는 수정 시 — 화면 모델 타입(I/T 접두사)과 상수
paths:
  - "**/features/*/types/**"
  - "**/features/*/constants/**"
  - "**/src/types/**"
  - "**/src/constants/**"
---

# Types · Constants Layer — 작성 규칙

> **코드 예시 안내**: 이 문서의 코드 예시는 **가상의 `notice`(공지사항) 기능 기준**이다 — 실제 파일은 없다. `notice`/`Notice` 를 자신의 `{domain}`/`{Domain}` 으로 바꿔 읽는다.

도메인 내부 의존 방향의 **최하단** (순서는 `architecture.md` 「도메인 내부 의존 방향」).
다른 모든 계층이 import 할 수 있고, **이 계층은 어떤 상위 계층도 import 하지 않는다.**

```
features/{domain}/
├── types/{domain}Type.ts            # 화면 모델·입력 타입 (I/T 접두사)
└── constants/{domain}Constants.ts   # 도메인 상수 (UPPER_SNAKE_CASE)

src/types/{name}Type.ts              # 공용 타입 (여러 도메인 공유)
src/constants/{name}Constants.ts     # 공용 상수
```

> 폴더는 필요할 때만 만든다 (빈 폴더 금지). 공용 `src/types/`·`src/constants/` 는 특정 도메인(`features/`) import 금지.
> 이 프로젝트 규칙이 전역 `~/.claude/rules/frontend/` 보다 우선한다.

---

## 1. `types/{domain}Type.ts` — 화면 모델 타입

**목표**: 프론트가 실제로 쓰는 **깔끔한 화면 모델**. 서버 DTO(`models/{domain}Schema.ts` 의 `T{Domain}Dto`)와 별개다.

### 규칙
- 파일명·타입 이름 규칙(`{name}Type.ts`, `I`/`T` 접두사, `Type` 접미사 금지)은 `naming-convention.md` 「타입」 — 예: `I{Domain}`, `I{Domain}Page`, `ICreate{Domain}Input`, `TUpdate{Domain}Input`.
- 모든 키 `camelCase`, 배열 필드는 `List` 접미사(`itemList`). 날짜는 `Date` 객체 (string 아님). nullable 백엔드 필드는 가능하면 optional(`?`)로 통일.
- 응답 모델(`I{Domain}`, 목록 축소형 `I{Domain}Summary`, 페이지 `I{Domain}Page`)과 입력 모델(`ICreate{Domain}Input`, `TUpdate{Domain}Input`) 분리.
- **Zod 스키마 만들지 말 것 — `interface`/`type` 만.** Mapper 가 검증된 DTO 에서 만든 산출물이라 런타임 검증할 untrusted 입력이 없다. 검증은 `models/{domain}Schema.ts` 에서 한 번만.
- **아무것도 import 하지 않는 것이 기본** (같은 계층의 `constants/` 만 예외). DTO 타입 import 금지.
- 컴포넌트 전용 Props 타입은 컴포넌트 파일 상단에 둔다. 여러 파일이 공유하면 그 컴포넌트 폴더 안 `{name}Type.ts`(예: `components/shared/{Name}/{name}Type.ts`).

### 예시 (가상의 `notice` 기능 기준 — 실제 파일 없음)
```ts
// features/notice/types/noticeType.ts — 프론트 친화 Domain model (camelCase, Date 객체)

export interface INoticeSummary {
  id: number;
  title: string;
  application: string;
  author: string;
  viewCount: number;
  createdAt: Date;
}

export interface INotice extends INoticeSummary {
  content: string;
  updatedAt: Date;
}

export interface INoticePage {
  itemList: INoticeSummary[];
  currentPage: number;
  numPages: number;
  pageSize: number;
  totalCount: number;
  hasPrevious: boolean;
  hasNext: boolean;
}

export interface ICreateNoticeInput {
  title: string;
  content: string;
  application: string;
}

export type TUpdateNoticeInput = Partial<ICreateNoticeInput>;

// 목록 조회 조건 — services(요청)·queries(키)·hooks(인자)가 함께 쓰므로 최하단 types 에 둔다
export interface INoticePageParams {
  page?: number;
  pageSize?: number;
  application?: string;
}
```

> 조회 조건(`I{Domain}PageParams`)처럼 **여러 계층이 공유하는 타입은 반드시 `types/`** 에 둔다. services·queries 에 각자 선언하면 중복되고, services 는 queries 를 import 할 수 없어 합칠 수도 없다.

---

## 2. `constants/{domain}Constants.ts` — 상수

### 규칙
- 상수 이름 **UPPER_SNAKE_CASE**. 상수 모음 객체는 이름 UPPER, 키 camelCase.
- 목록은 `as const` 배열 + `(typeof X)[number]` 로 유니온 타입 파생 (`T` 접두사).
- 매직 넘버·문자열·화면 고정 문구 중 **여러 파일이 공유하는 것**만 여기로. 한 컴포넌트에서만 쓰면 그 파일 상단 상수로 충분.
- 런타임 로직(함수·계산) 금지 — 값만.

### 예시 (가상의 `notice` 기능 기준 — 실제 파일 없음)
```ts
// features/notice/constants/noticeConstants.ts — notice 도메인 상수
// 카테고리 목록 API가 백엔드에 없어 프론트 상수로 관리 (백엔드 시드 데이터 기준, 변경 시 여기만 수정)
export const NOTICE_CATEGORY_LIST = ['일반', '이벤트', '기타'] as const;

export type TNoticeCategory = (typeof NOTICE_CATEGORY_LIST)[number];

export const NOTICE_CATEGORY_ALL_LABEL = '전체';
export const NOTICE_CATEGORY_PLACEHOLDER = '카테고리를 선택해주세요.';
```

---

## 사용처

| 계층 | 사용 |
|---|---|
| `models/` | Mapper 의 반환·입력 타입으로 `I{Domain}`·`ICreate{Domain}Input` import |
| `services/` | 메서드 시그니처에 화면 모델만 노출 |
| `queries/`·`hooks/` | `UseQueryResult<I{Domain}Page, Error>` 등 반환 타입 |
| `components/`·`pages/` | props·상수 |

---

## 체크리스트

- [ ] 파일명 `{name}Type.ts` / `{name}Constants.ts`? (`.d.ts` 아님)
- [ ] `interface` 는 `I`, `type` 은 `T` 접두사? `Type` 접미사 없음?
- [ ] 화면 모델이 camelCase + `Date` 객체?
- [ ] Zod 스키마·DTO 타입이 섞여 있지 않음? (그건 `models/`)
- [ ] 상위 계층(models·services·queries·hooks·components) import 없음?
- [ ] 상수 UPPER_SNAKE_CASE, 목록은 `as const` + 파생 유니온?
- [ ] 공용 `src/types/`·`src/constants/` 가 `features/` 를 import 하지 않음?

## 금지 사항

- ❌ `types/`·`constants/` 에서 다른 계층 import (최하단 계층 — ESLint 에러)
- ❌ `.d.ts` 타입 파일, `Type` 접미사 타입 이름 (`BoardColumnType` ❌ → `IBoardColumn`)
- ❌ 화면 모델에 `snake_case` 키·ISO 문자열 날짜
- ❌ 상수 파일에 함수·계산 로직
