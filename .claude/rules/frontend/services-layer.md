---
description: features/{domain}/services/ 또는 src/services/ 폴더 내 파일({domain}Service.ts) 작성 또는 수정 시 — API 호출 + safeParse + Mapper 변환
paths:
  - "**/features/*/services/**/*.ts"
  - "**/features/*/services/**/*.tsx"
  - "**/src/services/**"
---

# Services Layer — 작성 규칙

> **코드 예시 안내**: 이 문서의 코드 예시는 **가상의 `notice`(공지사항) 기능 기준**이다 — 실제 파일은 없다. `notice`/`Notice` 를 자신의 `{domain}`/`{Domain}` 으로 바꿔 읽는다.

`features/{domain}/services/` 는 **API 호출(`axiosInstance`) + DTO `safeParse` + Mapper 변환 + 비즈니스 로직** 을 담당한다.
**HTTP 호출이 허용되는 유일한 계층** (`axios.md`). 위 계층(queries·hooks·components)은 service 싱글톤 메서드만 부른다.

```
features/{domain}/services/
├── {domain}Service.ts                  # class {Domain}Service + 싱글턴 {domain}Service
└── __tests__/{domain}Service.test.ts   # MSW
```

> 공용 `src/services/` 는 도메인 무관 API(예: 파일 업로드)만 둔다. 특정 도메인 import 금지.

---

## 의존 방향

전체 순서·store 예외는 `architecture.md` 「도메인 내부 의존 방향」 (단일 출처). 이 계층 기준:

- `services/` → `types/`·`constants/`·`models/`·`utils/`·`@/lib/axios`·`@/utils/errors` 만 import.
- `queries/`·`store/`·`hooks/`·`components/` import 금지 (ESLint 에러).

---

## 핵심 원칙

1. **class + 싱글턴** — `export class {Domain}Service { … }` 정의 후 파일 하단에서 `export const {domain}Service = new {Domain}Service();`. 상위 계층은 싱글턴만 import.
2. **인터페이스 분리·DI 금지** — `I{Domain}Service.ts`·생성자 주입·`this.http` 추상화 없음. 메서드 안에서 `axiosInstance` 를 그대로 호출. 테스트는 MSW 가 가로챈다.
3. **`safeParse` 만** (`parse` 금지) — 실패 시 응답은 `throwDomainError(endpoint, error)`, 요청 payload 는 `new DomainLayerError(...)`.
4. **에러 분류 2종** (`@/utils/errors`) — HTTP/네트워크는 `DataLayerError`, 스키마 검증 실패는 `DomainLayerError`.
5. **반환은 화면 모델(`types/`)만** — DTO 를 시그니처/반환에 노출 금지.
6. **React·캐시 무지** — `queryClient`·React·Zustand import 금지. 캐시 키·무효화는 `queries/`·`hooks/` 책임.
7. **swagger/docs.md 선행 확인 — 호출 메서드 1개 = 엔드포인트 1개** (여러 API 를 조합하는 메서드는 이 호출 메서드들을 불러 조합한다 — 원칙 11) — 작성 전 `frontend/swagger/docs.md` 해당 도메인 섹션의 request/response body, status code, nullable 을 확인. 요청 body 가 있으면 요청 스키마, 응답 body 가 있으면 응답 스키마를 `models/{domain}Schema.ts` 에 한 쌍으로 둔다. 응답 본문 없는 엔드포인트(`data: null`)는 응답 스키마 생략.
8. **양방향 `safeParse`** — 요청: `{Domain}Mapper.to[Create|Update]Dto(input)` → `…RequestDtoSchema.safeParse` → 실패 시 `DomainLayerError` (요청 전 차단). 응답: `getEnvelopeData(data)` → `…DtoSchema.safeParse` → Mapper.
9. **검증은 `try` 밖에서** — `safeParse` 를 `try` 안에 넣으면 `DomainLayerError` 가 `DataLayerError` 로 둔갑한다.
10. **envelope 벗기기** — 백엔드 성공 응답은 `{ status, data }`. `getEnvelopeData(body)` 로 `data` 만 꺼내 스키마에 넘긴다.
11. **비즈니스 로직** — 여러 API 조합(직접 `axiosInstance` 를 여러 번 부르지 않고 같은 service 의 호출 메서드를 조합), 응답값 기반 계산 등 **서버 호출이 걸린** 도메인 로직은 service 메서드에 둔다. 서버 호출 없이 클라이언트 상태만 다루는 도메인 로직(예: 초안 자동저장)은 `hooks/` (`hooks-layer.md` 「3. 비즈니스 로직 훅」).

---

## 예시 (가상의 `notice` 기능 기준 — 실제 파일 없음)

```ts
// features/notice/services/noticeService.ts — API 호출 + safeParse + Mapper 변환 전담
import axios from 'axios';

import { axiosInstance } from '@/lib/axios';
import { DataLayerError, DomainLayerError, throwDomainError } from '@/utils/errors';

import type {
  ICreateNoticeInput,
  INotice,
  INoticePage,
  INoticePageParams,
} from '../types/noticeType';
import { NoticeMapper } from '../models/noticeMapper';
import {
  CreateNoticeRequestDtoSchema,
  NoticeDtoSchema,
  NoticeListResponseDtoSchema,
} from '../models/noticeSchema';

export class NoticeService {
  /** GET /api/notices — 목록 조회 (표준 페이지네이션) */
  async getPage(params: INoticePageParams = {}): Promise<INoticePage> {
    const body = await requestBody(
      () => axiosInstance.get('/api/notices', { params: convertPageQuery(params) }),
      'Failed to fetch notice list',
    );
    const parsed = NoticeListResponseDtoSchema.safeParse(getEnvelopeData(body));
    if (!parsed.success) throwDomainError('GET /api/notices', parsed.error);
    return NoticeMapper.toDomainList(parsed.data);
  }

  /** POST /api/notices — 생성 (staff 전용) */
  async create(input: ICreateNoticeInput): Promise<INotice> {
    const payload = CreateNoticeRequestDtoSchema.safeParse(NoticeMapper.toCreateDto(input));
    if (!payload.success) throw new DomainLayerError('Invalid create payload', payload.error);

    const body = await requestBody(
      () => axiosInstance.post('/api/notices', payload.data),
      'Failed to create notice',
    );
    const parsed = NoticeDtoSchema.safeParse(getEnvelopeData(body));
    if (!parsed.success) throwDomainError('POST /api/notices', parsed.error);
    return NoticeMapper.toDomain(parsed.data);
  }

  /** DELETE /api/notices/{id} — 삭제 (응답 data null) */
  async delete(noticeId: number): Promise<void> {
    await requestBody(
      () => axiosInstance.delete(`/api/notices/${noticeId}`),
      'Failed to delete notice',
    );
  }

  // getById / replace(PUT) / update(PATCH) / bulkDelete 도 같은 패턴
}

/** HTTP 호출만 try 로 감싸 응답 body 반환 — 실패는 DataLayerError 로 일원화 (검증은 호출부의 try 밖에서) */
async function requestBody(send: () => Promise<{ data: unknown }>, message: string): Promise<unknown> {
  try {
    const { data } = await send();
    return data;
  } catch (error) {
    throw toDataLayerError(error, message);
  }
}

/** 화면 조회 조건 → 백엔드 쿼리 파라미터 (kebab-case 키) */
function convertPageQuery(params: INoticePageParams): Record<string, unknown> {
  return { page: params.page, 'page-size': params.pageSize, application: params.application };
}

/** 성공 envelope({ status, data })에서 data 내부만 추출 — 형태가 다르면 그대로 반환해 safeParse가 잡게 한다 */
function getEnvelopeData(body: unknown): unknown {
  if (typeof body === 'object' && body !== null && 'data' in body) {
    return (body as { data: unknown }).data;
  }
  return body;
}

/** HTTP/네트워크 에러 → DataLayerError로 일원화 (검증 에러는 여기 거치지 않는다)
 *  백엔드 fail/error envelope({ status, data: { code, message } })의 message 를 serverMessage 로 담는다 (error-toast 스킬) */
function toDataLayerError(error: unknown, message: string): DataLayerError {
  if (!axios.isAxiosError(error)) return new DataLayerError(message, { cause: error });
  const serverMessage = (error.response?.data as { data?: { message?: unknown } } | undefined)?.data?.message;
  return new DataLayerError(message, {
    status: error.response?.status,
    serverMessage: typeof serverMessage === 'string' ? serverMessage : undefined,
    cause: error,
  });
}

export const noticeService = new NoticeService();
```

> 쿼리 파라미터는 백엔드 규약대로 kebab-case 키로 보낸다 (`convertPageQuery` — `'page-size'`).
> 메서드는 15줄 이내(`javascript-convention.md`) — HTTP 호출·에러 변환은 파일 하단 모듈 함수(`requestBody`·`toDataLayerError`·`getEnvelopeData`)로 뺀다.
> 업로드·다운로드는 `requestConfig('form' | 'blob')` 를 함께 넘긴다 (`axios.md`).

---

## 테스트 (MSW)

```ts
// features/{domain}/services/__tests__/{domain}Service.test.ts
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

import { axiosInstance } from '@/lib/axios';
import { DataLayerError, DomainLayerError } from '@/utils/errors';

import { noticeService } from '../noticeService';

// 실제 인스턴스의 baseURL 을 그대로 써야 env(NEXT_PUBLIC_API_URL)가 바뀌어도 MSW가 가로챈다
const BASE = axiosInstance.defaults.baseURL;

const server = setupServer();

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
  vi.spyOn(console, 'error').mockImplementation(() => {}); // throwDomainError 로그 소음 차단
});
afterEach(() => server.resetHandlers());
afterAll(() => {
  server.close();
  vi.restoreAllMocks();
});

describe('noticeService.getPage', () => {
  it('정상 응답 → INoticePage (Date 변환 포함)', async () => {
    server.use(http.get(`${BASE}/api/notices`, () => HttpResponse.json(listEnvelope)));
    const page = await noticeService.getPage({ page: 1, pageSize: 20 });
    expect(page.itemList[0].createdAt).toBeInstanceOf(Date);
  });

  it('스키마 불일치 → DomainLayerError', async () => {
    server.use(http.get(`${BASE}/api/notices`, () => HttpResponse.json(brokenEnvelope)));
    await expect(noticeService.getPage()).rejects.toBeInstanceOf(DomainLayerError);
  });

  it('5xx → DataLayerError', async () => {
    server.use(http.get(`${BASE}/api/notices`, serverError));
    await expect(noticeService.getPage()).rejects.toBeInstanceOf(DataLayerError);
  });

  it('네트워크 에러 → DataLayerError', async () => {
    server.use(http.get(`${BASE}/api/notices`, () => HttpResponse.error()));
    await expect(noticeService.getPage()).rejects.toBeInstanceOf(DataLayerError);
  });
});
```

**메서드별 4가지 케이스**: 성공 / 스키마 불일치 → `DomainLayerError` / HTTP 에러 → `DataLayerError` / 네트워크 에러 → `DataLayerError`. 요청 body 가 있으면 **잘못된 입력 → 요청 전 `DomainLayerError`** 와 **보낸 body 가 snake_case DTO 인지**도 확인.
**테스트 대상 아님**: Mapper 변환 세부(models 테스트), queryClient 캐시(queries·hooks 테스트), 컴포넌트.

---

## 체크리스트

- [ ] `swagger/docs.md` 해당 도메인 섹션을 실제로 읽고 작성?
- [ ] 엔드포인트마다 `models/{domain}Schema.ts` 에 요청·응답 스키마 한 쌍? (본문 없는 케이스 제외)
- [ ] `create`/`replace`/`update` 가 Mapper `to*Dto` + 요청·응답 양쪽 `safeParse`?
- [ ] `class {Domain}Service` + 하단 싱글턴 `{domain}Service` export? 인터페이스·DI 없음?
- [ ] `axiosInstance` 를 메서드 안에서 직접 호출? (`@/lib/axios`)
- [ ] 검증은 모두 `safeParse`, `try` **밖**에서? (`parse` 0건 — try 는 `requestBody` 안의 HTTP 호출만)
- [ ] 메서드 15줄 이내? 조회 조건 타입(`I{Domain}PageParams`)은 `types/` 에서 import?
- [ ] 응답은 `getEnvelopeData` 로 envelope 의 `data` 만 검증?
- [ ] 에러는 `@/utils/errors` 의 `DataLayerError`·`DomainLayerError`·`throwDomainError`?
- [ ] DTO 타입이 메서드 시그니처에 노출되지 않음? (반환은 `types/` 화면 모델)
- [ ] `queryClient`·React·Zustand import 없음? `queries/` 이상 import 없음?
- [ ] 테스트가 export 된 싱글턴을 그대로 사용하고 메서드별 4케이스 커버?
- [ ] `pnpm test src/features/{domain}/services` 통과?

## 금지 사항

- ❌ services 밖(queries·hooks·components·pages)에서 `axiosInstance`·`axios` 호출 (ESLint 에러 — `axios.md`)
- ❌ `I{Domain}Service` 인터페이스·Mock 클래스·생성자 주입
- ❌ `parse()` / `try` 안의 `safeParse`
- ❌ DTO 를 반환하거나 화면 모델을 Mapper 없이 손으로 조립
- ❌ 다른 도메인의 `services/` 직접 import (조합 규칙은 `architecture.md` 의 FEATURE_DEPENDENCIES)
