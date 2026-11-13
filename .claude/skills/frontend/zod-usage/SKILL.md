---
name: zod-usage
description: Zod 스키마로 검증 코드를 작성하거나 수정할 때 반드시 사용. API 응답/요청 검증(models/{domain}Schema.ts, services)과 폼 검증(utils/validation.ts + react-hook-form)에서 parse/safeParse 선택 기준과 에러 처리 방식을 정한다.
---

# Zod 사용 규칙 — parse vs safeParse

용도에 따라 딱 두 가지로 갈린다. 섞어 쓰지 않는다.

## 1. API 응답/요청 검증 → `safeParse` + `DomainLayerError` + console 로그

- 위치: `features/{domain}/services/{domain}Service.ts` (스키마는 `models/{domain}Schema.ts`)
- 이유: 백엔드 응답은 신뢰할 수 없는 외부 입력. throw 위치가 예측 불가능한 `parse`는 금지.
- 실패 시:
  1. **어떤 API에서, 어떤 항목이** 깨졌는지 `console.error`로 출력 — `[메서드 경로]` + `flatten().fieldErrors`
  2. `DomainLayerError`를 명시적으로 throw — try/catch **밖에서** 분기

```ts
// utils/errors.ts — 공용 헬퍼 (모든 service가 사용)
export function throwDomainError(endpoint: string, error: ZodError): never {
  console.error(`[DomainLayerError] ${endpoint} 응답 스키마 불일치`, error.flatten().fieldErrors);
  throw new DomainLayerError(`Invalid response: ${endpoint}`, error);
}
```

```ts
// service 사용 예 (features/post/services/postService.ts)
const parsed = PostDtoSchema.safeParse(data);
if (!parsed.success) throwDomainError(`GET /api/posts/${id}`, parsed.error);
return PostMapper.toDomain(parsed.data);
```

## 2. 폼 검증 → `parse` 스키마 + 항상 react-hook-form과 함께

- 위치: `features/{domain}/utils/validation.ts` (폼 전용 스키마 — API DTO 스키마 재사용 금지)
- 폼 스키마는 **항상 `zodResolver`로 react-hook-form에 연결**한다. 수동 `safeParse` 분기 금지 — 에러는 진짜 발생시켜 react-hook-form이 잡게 한다.
- 에러 표시는 두 곳에서:
  1. **필드 인라인** — `formState.errors.{field}.message` (스키마에 한국어 메시지 직접 작성)
  2. **toast 요약 1개** — 검증 실패로 제출이 막히면 `handleSubmit`의 `onInvalid`에서 `toast.error(...)` (→ `error-toast` 스킬 참고)

```ts
// features/{domain}/utils/validation.ts
export const postFormSchema = z.object({
  title: z.string().min(1, '제목을 입력하세요').max(255, '제목은 255자 이내'),
});
export type TPostFormValues = z.infer<typeof postFormSchema>;
```

```tsx
// 컴포넌트
const form = useForm<TPostFormValues>({ resolver: zodResolver(postFormSchema) });

const handleValid = (values: TPostFormValues) => mutate(values);
const handleInvalid = () => toast.error('입력 내용을 확인해주세요');

<form onSubmit={form.handleSubmit(handleValid, handleInvalid)}>
  <input {...form.register('title')} />
  {form.formState.errors.title && <p>{form.formState.errors.title.message}</p>}
</form>
```

## 금지

- ❌ service에서 `parse` 사용 / console 로그 없이 throw
- ❌ 폼에서 react-hook-form 없이 수동 `safeParse` 분기로 에러를 삼키기
- ❌ 폼 스키마와 API DTO 스키마 공유 (역할이 다름 — 폼은 사용자 메시지, DTO는 백엔드 1:1 묘사)
