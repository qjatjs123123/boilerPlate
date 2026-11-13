---
name: error-toast
description: 에러를 사용자에게 toast로 보여주는 코드를 작성할 때 사용. 백엔드 에러 메시지 vs 프론트 정의 메시지 선택 기준과 toast 노출 위치를 정한다.
---

# 에러 → Toast 표시 규칙

Toast UI: **디자인 킷(디자인 킷) Toast** — 서브모듈로 추후 도입 예정.
toast 호출은 반드시 **`@/lib/toast` 의 `toast`** 를 거친다 (실제 파일: `frontend/src/lib/toast.ts`).
디자인 킷 도입 전에는 표시 부품이 연결돼 있지 않아 **화면에 아무것도 뜨지 않는다** — 도입 시 `setToastHandler(디자인 킷 표시 함수)` 를 앱 시작 지점에서 1회 연결하면 호출부는 그대로 동작한다.

```ts
import { toast } from '@/lib/toast';
import { toUserMessage } from '@/utils/errors';
```

## 메시지 선택 기준 (핵심)

| 에러 출처 | 보여줄 메시지 |
|---|---|
| **백엔드 API가 에러 코드 + 메시지를 내려준 경우** | 백엔드가 건네준 에러 메시지 **그대로** |
| **프론트 자체 에러** (스키마 불일치, 네트워크, 코드 버그) | 프론트에서 정의한 메시지 (`toUserMessage`) |

```ts
// utils/errors.ts (실제 파일 — 문구는 모듈 상단 상수)
export function toUserMessage(error: unknown): string {
  // 1) 백엔드가 내려준 에러 메시지 우선 (toDataLayerError가 response body에서 추출해 담아둠)
  if (error instanceof DataLayerError && error.serverMessage) return error.serverMessage;

  // 2) 프론트 자체 에러 → 프론트 정의 메시지
  if (error instanceof DomainLayerError) return '데이터 처리 중 문제가 발생했습니다';
  if (error instanceof DataLayerError) return '요청에 실패했습니다. 잠시 후 다시 시도해주세요';
  return '알 수 없는 오류가 발생했습니다';
}
```

> 전제: service(`features/{domain}/services/`)의 `toDataLayerError`가 백엔드 실패 envelope `{ status: 'fail' | 'error', data: { code, message } }` 의 `error.response?.data?.data?.message` 를 `serverMessage`로 추출해 `DataLayerError`에 담는다 (`services-layer.md` 예시).

## 노출 위치 규칙

1. **toast 호출은 컴포넌트(호출부)에서만** — mutation 결과는 `mutate` 의 `onSuccess`/`onError`, 폼 검증 실패는 아래 2번의 `onInvalid`. 훅(`hooks/`)·service·interceptor 내부 금지.

```tsx
mutate(input, {
  onSuccess: () => toast.success('저장되었습니다'),
  onError: (error) => toast.error(toUserMessage(error)),
});
```

2. **폼 검증 에러는 react-hook-form이 처리 + 요약 toast 1개** — 필드별 메시지는 `formState.errors` 인라인, 제출이 막힌 사실만 `onInvalid`에서 toast (→ `zod-usage` 스킬 참고).

3. **조회(`useQuery`) 실패는 toast 금지** — `QueryBoundary`의 error 슬롯이 담당.

## 금지

- ❌ `lib/toast.ts` 래퍼 없이 toast 라이브러리 직접 import
- ❌ 훅·service·interceptor에서 toast 호출 (표시는 UI 계층 책임)
- ❌ 백엔드 메시지가 없는데 `error.message` 원문(스택/영문 에러)을 toast에 그대로 출력
