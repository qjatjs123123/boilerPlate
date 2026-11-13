---
description: features/{domain}/store/ 또는 src/store/ 폴더 내 Zustand store 작성 또는 수정 시 — 클라이언트 전역 상태
paths:
  - "**/features/*/store/**"
  - "**/src/store/**"
---

# Store Layer — 작성 규칙 (Zustand)

**서버 데이터가 아닌 클라이언트 상태** 중 여러 컴포넌트가 공유해야 하는 것만 둔다 (예: 선택된 탭, 모달 열림, 작성 중 초안).

```
features/{domain}/store/use{Domain}{Target}Store.ts   # 도메인 전역 상태
src/store/use{Target}Store.ts                         # 앱 공용 상태 (도메인 무관)
```

> **Zustand 는 아직 미설치** — 처음 store 가 필요할 때 `cd frontend && pnpm add zustand`. 필요 없으면 폴더도 만들지 않는다.

---

## 의존 방향

전체 순서·store 예외는 `architecture.md` 「도메인 내부 의존 방향」 (단일 출처). 이 계층 기준:

- `store/` → `types/`·`constants/`·`utils/`·`lib/` 만 import. 순서상 아래인 `models/`·`services/`·`queries/` 도 **금지** — store 는 서버 데이터·API 를 모르는 순수 클라이언트 상태다. `hooks/`·`components/`·`pages/` 도 금지 (모두 ESLint 에러).
- 공용 `src/store/` 는 `features/` import 금지.

---

## 핵심 원칙

1. **서버 상태는 넣지 않는다** — 서버 데이터는 TanStack Query 캐시(`queries/`·`hooks/`)가 단일 출처. store 에 복사 금지.
2. **먼저 로컬 state 를 고려** — 한 컴포넌트(또는 부모-자식)만 쓰면 `useState`. 끌어올림·합성으로 안 될 때만 store.
3. **store 1개 = 관심사 1개**, 파일명·훅 이름 `use{Domain}{Target}Store`.
4. **상태와 액션을 함께 선언**, 액션 이름은 동사 (`setCategory`, `resetSelection`). 불변 업데이트.
5. **selector 로 구독** — `use{Domain}FilterStore((state) => state.category)`. 스토어 전체 구독 금지 (불필요한 리렌더).
6. **부수효과·API 호출 금지** — 액션 안에서 service·axios 호출하지 않는다.

```ts
// features/{domain}/store/use{Domain}FilterStore.ts
import { create } from 'zustand';

interface I{Domain}FilterState {
  category?: string;
  setCategory: (category?: string) => void;
  resetFilter: () => void;
}

/** [{domain} 필터] 목록·헤더가 공유하는 카테고리 선택 상태 */
export const use{Domain}FilterStore = create<I{Domain}FilterState>((set) => ({
  category: undefined,
  setCategory: (category) => set({ category }),
  resetFilter: () => set({ category: undefined }),
}));
```

---

## 테스트

- 위치: `features/{domain}/store/__tests__/use{Domain}{Target}Store.test.ts`.
- 렌더링 없이 `use{Domain}FilterStore.getState()` 로 액션 호출 → 상태 검증. 테스트 간 오염 방지를 위해 `beforeEach` 에서 `use{Domain}FilterStore.setState(초기값)` 로 리셋.

```ts
beforeEach(() => use{Domain}FilterStore.setState({ category: undefined }));

it('setCategory 후 resetFilter 하면 초기값으로 돌아간다', () => {
  use{Domain}FilterStore.getState().setCategory('일반');
  use{Domain}FilterStore.getState().resetFilter();
  expect(use{Domain}FilterStore.getState().category).toBeUndefined();
});
```

---

## 체크리스트

- [ ] 정말 여러 컴포넌트가 공유하는 클라이언트 상태인가? (서버 데이터·로컬 state 아님)
- [ ] `zustand` 를 필요할 때만 설치했는가?
- [ ] 이름 `use{Domain}{Target}Store`, 관심사 1개?
- [ ] 소비부가 selector 로 필요한 값만 구독?
- [ ] 액션 안에 API 호출·부수효과 없음? `models/`·`services/`·`queries/`·`hooks/` 이상 import 없음?
- [ ] 테스트: 액션 호출 전후 상태 검증 (`store/__tests__/`)?

## 금지 사항

- ❌ 서버 응답을 store 에 저장 (React Query 캐시와 이중 출처)
- ❌ store 액션에서 service·axios 호출
- ❌ `persist` 등 미들웨어를 이유 없이 기본 적용
- ❌ 공용 `src/store/` 에서 특정 도메인 import
