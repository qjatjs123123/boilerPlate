---
description: features/{domain}/hooks/ 또는 src/hooks/ 폴더 내 훅 작성 또는 수정 시 — 읽기 useRead*(useQuery + queries 의 queryOptions), 쓰기 useCreate/Update/Delete*(useMutation + queries 키 invalidate)
paths:
  - "**/features/*/hooks/**/*.ts"
  - "**/features/*/hooks/**/*.tsx"
  - "**/src/hooks/**"
---

# Hooks Layer — 작성 규칙 (도메인 읽기·쓰기 훅)

> **코드 예시 안내**: 이 문서의 코드 예시는 **가상의 `notice`(공지사항) 기능 기준**이다 — 실제 파일은 없다. `notice`/`Notice` 를 자신의 `{domain}`/`{Domain}` 으로 바꿔 읽는다.

`features/{domain}/hooks/` 는 **컴포넌트가 서버 데이터를 읽고 쓰는 유일한 창구**다.
- **읽기** `useRead{Domain}*` — `useQuery` + `queries/` 의 queryOptions 를 펼쳐 쓰고 캐시 정책만 덧붙인다.
- **쓰기** `useCreate/Update/Delete{Domain}`, `use{Action}{Domain}` — `useMutation` + 성공 시 `queries/` 의 키로 invalidate.

```
features/{domain}/hooks/
├── useRead{Domain}Page.ts         # 목록 (useQuery)
├── useRead{Domain}.ts             # 단건 (useQuery)
├── useCreate{Domain}.ts           # 생성 (useMutation)
├── useBulkDelete{Domain}.ts       # 동작 (useMutation)
└── __tests__/useRead{Domain}Page.test.tsx
```

> 파일 1개 = 훅 1개. 한 파일에 여러 쿼리·mutation 을 합치지 않는다.
> 공용 `src/hooks/` 는 도메인 무관 훅, 또는 여러 하위 도메인 조회를 단순 조합하는 훅(예: `useQnaAndFaq.ts`)만 — 이때 각 도메인의 **`queries/`(queryOptions) 만** import 한다 (services·hooks 등은 ESLint 에러). `architecture.md` 「도메인 간 의존」.

---

## 의존 방향

전체 순서·store 예외는 `architecture.md` 「도메인 내부 의존 방향」 (단일 출처). 이 계층 기준:

- `hooks/` → `queries/`·`services/`·`store/`·`types/`·`constants/`·`utils/` import 가능.
- `components/`·`pages/` import 금지 (ESLint 에러). `@/lib/axios` 직접 호출 금지 — service 경유.

---

## 핵심 원칙 (공통)

1. **queryKey 단일 출처** — 읽기의 queryKey 는 queryOptions 에서, 쓰기의 `invalidateQueries` 키는 **반드시 `queries/{domain}QueryKeys.ts` 의 `{domain}Keys`**. 인라인 배열 금지.
2. **service 싱글턴 직접 import** — `import { {domain}Service } from '../services/{domain}Service'`. axios 직접 호출 금지.
3. **화면 모델만 받고 반환** — DTO 노출 금지.
4. **결과를 가공하지 않고 그대로 반환** — `UseQueryResult` / `UseMutationResult`. UI 가 `isPending`·`isError`·`data` 분기 (`QueryBoundary`).
5. **부수효과(라우팅·토스트·`alert`·`window`)는 훅 안에서 직접 호출하지 않는다** — 호출부 `mutate(vars, { onSuccess, onError })` 로.
6. **suspense 모드 금지** (현재 정책) — RSC 와 혼선 방지.

---

## 1. 읽기 훅 — `useRead{Domain}*` (useQuery)

- `queries/{domain}Queries.ts` 의 queryOptions 를 **스프레드**하고, 캐시 정책(`staleTime`·`gcTime`·`placeholderData`·`enabled`)만 덧붙인다. queryKey·queryFn 을 훅에서 새로 쓰지 않는다.
- 반환 타입 명시: `UseQueryResult<I{Domain}Page, Error>`.
- 페이지 전환형 목록은 `placeholderData: keepPreviousData` 로 이전 데이터 유지.

```ts
// features/notice/hooks/useReadNoticePage.ts — 공지 목록 페이지 조회 (읽기 전용)
import { keepPreviousData, useQuery, type UseQueryResult } from '@tanstack/react-query';

import { noticePageQuery } from '../queries/noticeQueries';
import type { INoticePage, INoticePageParams } from '../types/noticeType';

/** 공지 목록 페이지 조회 — 페이지 전환 시 이전 데이터 유지(placeholderData) */
export function useReadNoticePage(
  params: INoticePageParams = {},
): UseQueryResult<INoticePage, Error> {
  return useQuery({
    ...noticePageQuery(params),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
    gcTime: 5 * 60_000,
  });
}
```

단건은 `useRead{Domain}(id, options?: { enabled? })` 로 `enabled: (options?.enabled ?? true) && Boolean(id)`. 무한스크롤은 `useInfiniteQuery({ ...{domain}ListInfiniteQuery(params) })` — 수동 page state 금지.

### 캐싱 정책 기본값

| 데이터 성격 | `staleTime` | `gcTime` |
|---|---|---|
| 단건 상세 | 60_000 | 5 * 60_000 |
| 피드 / 목록 | 30_000 | 5 * 60_000 |
| 거의 안 변함 (카테고리 등) | 5 * 60_000 | 30 * 60_000 |
| 내 정보 (`me`) | 0 | 5 * 60_000 |

`retry`·`refetchOnWindowFocus` 는 전역 `lib/ReactQueryProvider.tsx` 에만 (훅에서 재정의 금지).

### UI 소비 — `QueryBoundary` 로 단일 책임

표시 컴포넌트는 "데이터가 있을 때"만 그린다. 로딩·에러는 `components/layout/QueryBoundary` 가 흡수한다.

```tsx
const query = useReadNoticePage({ page, application });
return (
  <QueryBoundary query={query} pending={<BoardSkeleton loadingLabel="공지사항 불러오는 중" />}>
    {(noticePage) => <NoticeTable rowList={noticePage.itemList} />}
  </QueryBoundary>
);
```

- 표시 컴포넌트는 화면 모델만 props 로 받는다 — `isPending`·`isError` prop 금지.
- 여러 쿼리는 각각 `QueryBoundary` 로 감싼다. v5: `isLoading` 대신 **`isPending`**, 백그라운드 refetch 는 `isFetching`.
- `QueryBoundary` children 안에서 또 다른 `useQuery` 를 호출하지 않는다.

---

## 2. 쓰기 훅 — `useCreate/Update/Delete{Domain}`, `use{Action}{Domain}` (useMutation)

- `mutationFn` 은 service 메서드 한 줄 호출.
- `onSuccess` 에서 `queries/` 의 키로 invalidate / `setQueryData`.
- **낙관적 업데이트 금지** — `onMutate` 로 캐시를 미리 바꾸지 않는다. 항상 서버 응답 후 `onSuccess` 에서 갱신. 빠른 피드백은 버튼 `isPending` 으로 충분.

```ts
// features/notice/hooks/useBulkDeleteNotice.ts — 공지 일괄 삭제 mutation
import { useMutation, useQueryClient, type UseMutationResult } from '@tanstack/react-query';

import { noticeKeys } from '../queries/noticeQueryKeys';
import { noticeService } from '../services/noticeService';

/** 공지 일괄 삭제 — 성공 시 목록 캐시 전체 invalidate (삭제 개수 반환) */
export function useBulkDeleteNotice(): UseMutationResult<number, Error, number[]> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (noticeIdList: number[]) => noticeService.bulkDelete(noticeIdList),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: noticeKeys.lists.queryKey });
    },
  });
}
```

### Invalidation 패턴

> 표의 키는 모두 `.queryKey` 로 꺼내 쓴다 (예: `setQueryData(noticeKeys.details._ctx.byId(id).queryKey, updated)`).

| 작업 | invalidate / 수정 대상 |
|---|---|
| Create | `lists` invalidate + `setQueryData(details._ctx.byId(newId))` |
| Update | `setQueryData(details._ctx.byId(id), updated)` + `lists` invalidate |
| Delete | `removeQueries(details._ctx.byId(id))` + `lists` invalidate |
| Action (좋아요 등) | 응답값으로 `setQueryData(details._ctx.byId(id))` + 필요 시 `lists` invalidate |

- **루트(`{domain}Keys._def`)로 통째 invalidate 하지 말 것** — 과도한 refetch. 항상 `lists` / `details._ctx.byId(id)` 같은 구체 키.
- 다른 도메인 키 invalidate 가 필요하면 그 도메인이 `FEATURE_DEPENDENCIES` 로 허용된 하위 도메인일 때만 (`architecture.md`).

### 호출부 패턴

```tsx
const bulkDeleteMutation = useBulkDeleteNotice();

// 확인창은 호출부에서 — shadcn AlertDialog 의 확인 버튼 onClick 에 연결 (window.confirm 금지)
const handleDeleteConfirmClick = () => {
  bulkDeleteMutation.mutate(selectedIdList, {
    onSuccess: () => setSelectedIdList([]),                       // 화면 상태 정리도 호출부에서
    onError: (error) => toast.error(toUserMessage(error)),        // 토스트도 호출부에서 (error-toast 스킬)
  });
};
```

- 버튼 disabled·스피너는 `isPending`. 폼 전체 잠금은 `<fieldset disabled={isPending}>`.

---

## 3. 비즈니스 로직 훅 (서버 호출 없는 경우)

서버 변경이 없는 도메인 로직(예: `use{Domain}DraftAutosave`)도 이 폴더에 둔다. 파일명이 도메인 동작을 드러내야 하고, 데이터가 필요하면 위 읽기 훅을 합성한다. 도메인 store(`store/`) 접근 OK.

---

## 테스트

- 위치: `features/{domain}/hooks/__tests__/{hookName}.test.tsx` (`// @vitest-environment jsdom`).
- service 싱글턴을 `vi.mock('../../services/{domain}Service', …)` 으로 모킹, 테스트별 `QueryClient` + `QueryClientProvider` wrapper 로 `renderHook`.
- 읽기 검증: ① service 가 올바른 인자로 호출 ② 결과를 그대로 반환 ③ params 기준 queryKey 캐시에 저장·격리 ④ `enabled: false` 시 미호출 ⑤ 에러 시 `isError`.
- 쓰기 검증: ① `mutate` 시 service 메서드 인자 ② 성공 시 `invalidateQueries` 가 올바른 키로 호출(spy) ③ 에러 시 `isError` + 캐시 불변.

```tsx
vi.mock('../../services/noticeService', () => ({
  noticeService: { getPage: vi.fn() },
}));

/** 테스트별 독립 QueryClient + Provider wrapper 생성 */
function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  return { queryClient, wrapper };
}

// 쓰기 훅
const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
// ... mutate 후
expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: noticeKeys.lists.queryKey });
```

---

## 체크리스트

- [ ] 파일 1개 = 훅 1개? 이름이 `useRead*` / `useCreate·Update·Delete*` / `use{Action}*`?
- [ ] 읽기 훅이 `queries/` 의 queryOptions 를 스프레드? (훅에서 queryKey·queryFn 재작성 없음)
- [ ] 읽기 훅에 `staleTime`/`gcTime` 명시, `retry` 재정의 없음?
- [ ] `invalidateQueries` 키가 전부 `{domain}Keys` 에서 옴? 루트 `_def` invalidate 없음?
- [ ] service 싱글턴 직접 import? (`axiosInstance` 직접 호출 없음)
- [ ] 결과를 가공 없이 `UseQueryResult`/`UseMutationResult` 로 반환?
- [ ] 라우팅·토스트·confirm 이 훅 밖 호출부에 있음?
- [ ] `onMutate` 없음? (낙관적 업데이트 금지)
- [ ] `components/`·`pages/` import 없음? 다른 도메인 hooks import 없음?
- [ ] `pnpm test src/features/{domain}/hooks` 통과?

## 금지 사항

- ❌ 훅 안에서 인라인 queryKey (`['{domain}', page]`)
- ❌ 훅 안에서 `axiosInstance` 호출 / 응답 가공
- ❌ `onMutate` 낙관적 업데이트
- ❌ 훅 안에서 `router.push`·`toast`·`alert` 직접 호출
- ❌ 다른 도메인 `hooks/` import (조합은 공용 `src/hooks/` 또는 FEATURE_DEPENDENCIES 등록된 상위 도메인)
