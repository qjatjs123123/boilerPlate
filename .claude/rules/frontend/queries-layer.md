---
description: features/{domain}/queries/ 또는 src/queries/ 폴더 내 파일({domain}QueryKeys.ts, {domain}Queries.ts) 작성 또는 수정 시 — queryKey factory + queryOptions
paths:
  - "**/features/*/queries/**/*.ts"
  - "**/features/*/queries/**/*.tsx"
  - "**/src/queries/**"
---

# Queries Layer — 작성 규칙 (queryKey + queryOptions)

> **코드 예시 안내**: 이 문서의 코드 예시는 **가상의 `notice`(공지사항) 기능 기준**이다 — 실제 파일은 없다. `notice`/`Notice` 를 자신의 `{domain}`/`{Domain}` 으로 바꿔 읽는다.

`features/{domain}/queries/` 는 **TanStack Query v5 의 queryKey 와 queryFn 을 묶어 정의하는 계층**이다.
**훅(`useQuery`·`useMutation`)은 여기 두지 않는다** — 읽기·쓰기 훅은 `hooks/` (`hooks-layer.md`).

```
features/{domain}/queries/
├── {domain}QueryKeys.ts     # query key factory — 도메인 키의 단일 출처 ({domain}Keys)
└── {domain}Queries.ts       # queryOptions 함수 ({domain}{Target}Query(params))
```

> 공용 `src/queries/` 는 도메인 무관 쿼리(예: 공통 코드)만. 특정 도메인 import 금지.

---

## 의존 방향

전체 순서·store 예외는 `architecture.md` 「도메인 내부 의존 방향」 (단일 출처). 이 계층 기준:

- `queries/` → `services/`·`types/`·`constants/`·`utils/` 만 import. 조회 조건 타입(`I{Domain}PageParams`)도 `types/` 에서 가져온다 (여기서 선언하지 않는다).
- `store/`·`hooks/`·`components/` import 금지 (ESLint 에러). `@/lib/axios` 직접 호출 금지 — 반드시 service 싱글턴 경유.

---

## 핵심 원칙

1. **queryKey 단일 출처** — 도메인의 모든 키는 `{domain}QueryKeys.ts` 의 `{domain}Keys`. 인라인 배열·문자열 키 금지. 쓰기 훅의 `invalidateQueries` 도 여기서 import.
2. **queryOptions 로 key + fn 묶기** — `{domain}Queries.ts` 는 `queryOptions({ queryKey, queryFn })` 을 반환하는 함수만 export. 읽기 훅·상위 도메인·서버 prefetch 가 같은 정의를 재사용한다.
3. **queryFn 은 service 메서드 한 줄 호출** — 변환·계산 금지 (service 가 이미 safeParse + Mapper 를 거쳐 화면 모델 반환).
4. **캐시 정책은 훅에서** — queryOptions 에는 key·fn 만 둔다 (정책 기본값은 `hooks-layer.md` 「캐싱 정책 기본값」).
5. **React 훅 호출 금지** — 이 폴더의 함수는 순수 함수다 (`useQuery`·`useQueryClient` 없음).
6. **상위 도메인 조합 지점** — 다른 도메인이 이 도메인 데이터를 조합해야 하면 `{domain}Queries.ts` 의 queryOptions 를 가져다 쓴다 (`FEATURE_DEPENDENCIES` 등록 필요 — `architecture.md`).

---

## 1. `{domain}QueryKeys.ts` — Query Key Factory

`@lukemorales/query-key-factory` 사용 (이미 설치). export 이름 `{domain}Keys`. 파라미터는 객체 하나, `cursor` 는 키에 넣지 않는다.
**목록 키는 `lists` 의 `contextQueries` 하위에** 둔다 — `lists.queryKey` 하나로 모든 페이지 키를 프리픽스 매칭해 invalidate 할 수 있다 (병렬 선언 시 매칭 불가).

```ts
// features/notice/queries/noticeQueryKeys.ts — notice 도메인 queryKey 단일 출처
import { createQueryKeys } from '@lukemorales/query-key-factory';

import type { INoticePageParams } from '../types/noticeType'; // 조회 조건은 types 에 단일 정의

// list 키를 lists 하위(contextQueries)에 두어 lists.queryKey invalidation이
// 모든 페이지 키에 프리픽스 매칭되도록 한다 (병렬 선언 시 매칭 불가).
export const noticeKeys = createQueryKeys('notice', {
  lists: {
    queryKey: null,
    contextQueries: {
      page: (params: INoticePageParams) => ({ queryKey: [{ ...params }] }),
    },
  },
  details: {
    queryKey: null,
    contextQueries: {
      byId: (noticeId: number) => ({ queryKey: [noticeId] }),
    },
  },
});
```

사용:
```ts
noticeKeys.lists._ctx.page(params).queryKey   // 특정 페이지
noticeKeys.details._ctx.byId(id).queryKey     // 특정 상세
noticeKeys.lists.queryKey                     // 모든 목록 (invalidate 용)
```

---

## 2. `{domain}Queries.ts` — queryOptions

이름: `{domain}{Target}Query(params)` (예: `{domain}PageQuery`, `{domain}DetailQuery`). JSDoc 한 줄 (형식은 `javascript-convention.md` 「주석」).

```ts
// features/notice/queries/noticeQueries.ts — notice 도메인 queryKey + queryFn 묶음 (queryOptions)
// 상위 도메인이 notice 데이터를 조합할 때도 이 함수를 가져다 쓴다.
import { queryOptions } from '@tanstack/react-query';

import { noticeService } from '../services/noticeService';
import type { INoticePageParams } from '../types/noticeType';
import { noticeKeys } from './noticeQueryKeys';

/** [공지 목록] 페이지 조회 queryKey·queryFn */
export function noticePageQuery(params: INoticePageParams = {}) {
  return queryOptions({
    queryKey: noticeKeys.lists._ctx.page(params).queryKey,
    queryFn: () => noticeService.getPage(params),
  });
}
```

> 무한스크롤은 `infiniteQueryOptions({ queryKey, queryFn: ({ pageParam }) => …, initialPageParam, getNextPageParam })` 로 같은 파일에 둔다.

소비 (`hooks/useRead{Domain}Page.ts` — 자세한 규칙은 `hooks-layer.md`):
```ts
return useQuery({ ...noticePageQuery(params), placeholderData: keepPreviousData, staleTime: 30_000 });
```

---

## 테스트

- queryKey 구조는 읽기 훅 테스트(`hooks/__tests__/useRead*.test.tsx`)에서 함께 검증한다 — 별도 파일 불필요.
- 반드시 확인: **`lists` 키가 page 키의 프리픽스**인지 (invalidate 매칭 보장).

```ts
it('lists 키가 page 키의 프리픽스다 — lists invalidation이 페이지 캐시에 매칭된다', () => {
  const listsKey = noticeKeys.lists.queryKey;
  const pageKey = noticeKeys.lists._ctx.page({ page: 1 }).queryKey;
  expect(pageKey.slice(0, listsKey.length)).toEqual([...listsKey]);
});
```

---

## 체크리스트

- [ ] 모든 키가 `{domain}Keys` 에서 옴? (인라인 배열·문자열 0건)
- [ ] 목록 키가 `lists.contextQueries` 하위? (`lists.queryKey` 로 프리픽스 invalidate 가능)
- [ ] queryKey 에 `cursor` 미포함?
- [ ] `{domain}Queries.ts` 가 `queryOptions` 반환 함수만 export? (`useQuery` 등 훅 없음)
- [ ] queryFn 이 service 싱글턴 메서드 한 줄 호출?
- [ ] `staleTime`·`gcTime` 등 캐시 정책은 훅에 있음? (queryOptions 엔 key·fn 만)
- [ ] `store/`·`hooks/`·`components/`·`@/lib/axios` import 없음?
- [ ] 다른 도메인 queries 조합 시 `FEATURE_DEPENDENCIES` 에 한 방향 등록?

## 금지 사항

- ❌ `queries/` 안에서 `useQuery`·`useMutation`·`useQueryClient` 호출 (훅은 `hooks/`)
- ❌ queryFn 에서 `axiosInstance` 직접 호출 / 응답 가공
- ❌ 전역 `lib/queryKeys.ts` 같은 도메인 통합 키 파일
- ❌ 하위 도메인이 상위 도메인 queries import (역방향 — `architecture.md`)
