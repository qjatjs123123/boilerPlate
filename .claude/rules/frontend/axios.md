---
description: lib/axios.ts 또는 features/*/services/*.ts·src/services/ 작성·수정 시 — axiosInstance 단일 진입점 + interceptor 뼈대, HTTP 호출은 services 에서만
paths:
  - "**/lib/axios.ts"
  - "**/features/*/services/**/*.ts"
  - "**/src/services/**"
---

# axios Client — 작성 규칙

`lib/axios.ts` 는 **HTTP 통신의 단일 진입점**. 모든 API 호출은 여기서 만든 `axiosInstance` 하나만 거친다. 본 rule은 **인스턴스 + interceptor의 뼈대(skeleton)만** 규정하고, 인증·리다이렉트 같은 **프로젝트별 정책은 TODO 슬롯으로 비워둔다**.

---

## 목적 — 왜 axios를 직접 import 하지 않는가

1. **baseURL · 인증 헤더 · 공통 에러 처리**를 한 곳에서 제어 → 흩어진 설정 충돌 방지.
2. **HTTP 클라이언트 교체**(axios → fetch / ky 등)는 `lib/axios.ts` 한 파일 + 각 service 만 수정.
3. **테스트**: MSW가 axios 호출을 가로채므로, 단일 인스턴스만 일관되게 쓰면 개별 mocking 불필요.

---

## 핵심 원칙 (강제)

1. **`axiosInstance`는 `lib/axios.ts`에서만 생성·export** — 다른 파일에서 `axios.create()` 호출 금지.
2. **`import { axiosInstance } from '@/lib/axios'` 는 `services/` 계층(도메인 `features/*/services/`, 공용 `src/services/`)에서만** — `queries/`·`hooks/`·`components/`·`pages/`·`app/` 에서 import 하면 ESLint 에러.
3. **`import axios from 'axios'` 의 유일한 예외**: 타입 가드 `axios.isAxiosError(error)` 호출 — `lib/axios.ts` 와 services 에서만 허용 (예: `{domain}Service.ts` 의 `toDataLayerError`). ESLint `no-restricted-imports` 가 그 외 파일을 막는다.
4. **interceptor는 `lib/axios.ts` 내부에서만 등록** — service / hook / 컴포넌트에서 `axiosInstance.interceptors.use(...)` 호출 금지. (등록 순서 꼬임 + 중복 등록 버그 방지)

---

## 뼈대 코드 — `lib/axios.ts` 템플릿

```ts
// lib/axios.ts
import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
  AxiosResponse,
  AxiosError,
} from 'axios';

const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const axiosInstance: AxiosInstance = axios.create({
  baseURL,
  withCredentials: true,                       // 쿠키 기반 인증 사용 시
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
});

// ─── Request Interceptor (보내기 전) ──────────────────────────────
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // TODO(project): 인증 헤더 / 트레이싱 ID / locale 등 주입
    // 예) const token = getAccessToken();
    //     if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error: AxiosError) => Promise.reject(error),
);

// ─── Response Interceptor (응답 후) ───────────────────────────────
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    // TODO(project): 응답 로깅, 공통 unwrap 등
    return response;
  },
  (error: AxiosError) => {
    // TODO(project): 401 리다이렉트 / 토큰 refresh 등 (토스트는 여기서 띄우지 않는다 — error-toast 스킬)
    // 예) if (error.response?.status === 401 && typeof window !== 'undefined') {
    //       window.location.href = '/login';
    //     }
    return Promise.reject(error);
  },
);

// ─── Content-Type 프리셋 ─────────────────────────────────────────
export type TRequestKind = 'json' | 'form' | 'blob' | 'text';

/**
 * 요청 종류에 따른 Content-Type / responseType 프리셋.
 * 호출부는 종류만 명시(`'form'` 등)하고, multipart boundary 같은 디테일은 여기서 일원화.
 */
export function requestConfig(kind: TRequestKind): AxiosRequestConfig {
  switch (kind) {
    case 'form':
      // multipart/form-data; boundary=... 는 브라우저가 자동 생성한다.
      // 'multipart/form-data' 문자열을 직접 적으면 boundary 누락 → 서버 파싱 실패.
      return { headers: { 'Content-Type': undefined as unknown as string } };
    case 'blob':
      return {
        headers: { 'Content-Type': 'application/octet-stream' },
        responseType: 'blob',
      };
    case 'text':
      return { headers: { 'Content-Type': 'text/html; charset=utf-8' } };
    case 'json':
    default:
      return { headers: { 'Content-Type': 'application/json' } };
  }
}
```

> **TODO 슬롯은 비워둔 채 머지해도 된다.** 프로젝트 정책(인증·리다이렉트 등)이 정해지면 그때 이 자리에 채운다. 뼈대는 유지.

---

## interceptor 작성 가이드 (TODO 슬롯을 채울 때의 원칙)

- **request interceptor는 절대 throw 하지 않는다** — 무조건 `config` 반환 또는 `Promise.reject(error)` 전달. throw 시 axios가 reject로 잡지 못하는 케이스 발생.
- **응답 본문을 interceptor에서 변형하지 않는다** — `safeParse` + Mapper 는 services 책임 (`models/` 의 스키마·Mapper 사용). interceptor는 transport 레벨만.
- **DOM 접근(`window.location` 등)은 SSR 가드 필수** — `typeof window !== 'undefined'` 확인 후 호출. RSC에서 실행되면 빌드/런타임 실패.
- **에러 객체를 새로 만들지 않는다** — `Promise.reject(error)` 로 원본 그대로 위임. `DataLayerError` 로의 변환은 service 의 `toDataLayerError` 에서 일원화.
- **interceptor 안에서 `axiosInstance` 재호출 금지** (무한 재귀 위험) — 토큰 refresh가 필요하면 **별도 `axios.create()` 인스턴스** 또는 `fetch` 사용.
- **로그는 환경 가드 후** — `if (process.env.NODE_ENV !== 'production') console.warn(...)`. 상시 `console.log` 금지.

---

## 요청 종류별 프리셋 — `requestConfig(kind)`

호출부는 **요청 종류만 단어로 명시**한다. Content-Type / responseType / multipart boundary 같은 디테일은 모두 `lib/axios.ts` 안의 `requestConfig` 헬퍼에 격리.

### 사용 규칙

1. **호출부에 `headers: { 'Content-Type': ... }` 인라인으로 적지 않는다** — 반드시 `requestConfig(kind)` 경유.
2. **JSON 은 인스턴스 default 와 동일** — 생략 가능. 명시하려면 `requestConfig('json')`.
3. **파일 업로드는 `requestConfig('form')`** — boundary 자동 부착은 헬퍼 안에서 처리.
4. **바이너리 다운로드는 `requestConfig('blob')`** — `responseType: 'blob'` 포함.
5. **새 종류가 필요하면 `requestConfig` 한 곳만 확장** — 호출부 코드는 단어 하나만 추가.

### service 호출 예시

```ts
// JSON (기본값 — 생략 가능)
await axiosInstance.post('/api/posts', payload);
// 또는 명시:
await axiosInstance.post('/api/posts', payload, requestConfig('json'));

// 파일 업로드 — multipart/form-data
const form = new FormData();
form.append('file', file);
await axiosInstance.post(`/api/posts/${id}/cover`, form, requestConfig('form'));

// 바이너리 다운로드
const { data: blob } = await axiosInstance.get(`/api/files/${id}`, requestConfig('blob'));

// 추가 옵션과 합치기 (진행률 등)
await axiosInstance.post(url, form, {
  ...requestConfig('form'),
  onUploadProgress: (e) => {
    if (e.total) onProgress(Math.round((e.loaded / e.total) * 100));
  },
});
```

### service 메서드 풀 템플릿 (업로드)

```ts
async uploadAvatar(file: File): Promise<I{Domain}> {
  const form = new FormData();
  form.append('file', file);

  const body = await requestBody(
    () => axiosInstance.post('/api/{domain}s/avatar', form, requestConfig('form')),
    'Failed to upload avatar',
  );
  const parsed = {Domain}DtoSchema.safeParse(getEnvelopeData(body));
  if (!parsed.success) throwDomainError('POST /api/{domain}s/avatar', parsed.error);
  return {Domain}Mapper.toDomain(parsed.data);
}
```

> `requestBody`·`getEnvelopeData`·`toDataLayerError` 는 service 파일 하단 모듈 함수 (`services-layer.md` 예시).
> `onUploadProgress` 콜백은 service 메서드 시그니처에서 옵션으로 받고, UI 상태 갱신은 호출부(컴포넌트 / hook)에서 담당.

---

## 금지 사항

- ❌ service / hook / 컴포넌트에서 `import axios from 'axios'` 후 `axios.get(...)` 직접 호출.
  - 단, services 의 `axios.isAxiosError(error)` 타입 가드는 허용.
- ❌ `components/`·`pages/`·`hooks/`·`queries/`·`store/`·`app/` 에서 `axiosInstance` 를 import·호출 — 반드시 service 를 경유 (ESLint 에러).
- ❌ `lib/axios.ts` 외 다른 파일에서 `axiosInstance.interceptors.use(...)` 호출.
- ❌ interceptor 안에서 응답 데이터 `parse` / 스키마 검증 / DTO → Domain 매핑.
- ❌ 여러 인스턴스(`adminAxios`, `publicAxios`) 무분별 export — 정말 필요한 경우만, 그때도 `lib/axios.ts` 안에서 명시적으로.
- ❌ 호출부에서 `headers: { 'Content-Type': ... }` 인라인 작성 — 반드시 `requestConfig(kind)` 경유.
- ❌ `'Content-Type': 'multipart/form-data'` 문자열 직접 작성 — boundary 누락. `requestConfig('form')` 사용.

---

## 체크리스트

- [ ] `lib/axios.ts` 외 파일에서 `import axios from 'axios'` 없음? (`axios.isAxiosError` 가드 제외)
- [ ] 모든 HTTP 호출이 `axiosInstance` 를 거치고, services 계층에서만 발생?
- [ ] `axiosInstance.interceptors.*.use(...)` 호출이 `lib/axios.ts` 안에만 있음?
- [ ] request interceptor가 항상 `config` 반환 (throw 없음)?
- [ ] response 에러 interceptor가 `Promise.reject(error)` 로 원본을 전달?
- [ ] DOM 접근에 `typeof window !== 'undefined'` 가드?
- [ ] interceptor에서 응답 본문 변형 / 스키마 검증 없음?
- [ ] interceptor 내부에서 `axiosInstance` 를 재호출하지 않음?
- [ ] 호출부에 `headers: { 'Content-Type': ... }` 인라인 작성 없음? 모두 `requestConfig(kind)` 경유?
- [ ] `'multipart/form-data'` 문자열 직접 작성 0건? 업로드는 `requestConfig('form')` 사용?
