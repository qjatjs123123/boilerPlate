---
description: features/{domain}/models/ 또는 src/models/ 폴더 내 파일({domain}Schema.ts, {domain}Mapper.ts) 작성 또는 수정 시 — Zod 스키마 + Mapper (ACL·Adapter 계층)
paths:
  - "**/features/*/models/**/*.ts"
  - "**/features/*/models/**/*.tsx"
  - "**/src/models/**"
---

# Models Layer — 작성 규칙 (Zod 스키마 + Mapper)

> **코드 예시 안내**: 이 문서의 코드 예시는 **가상의 `notice`(공지사항) 기능 기준**이다 — 실제 파일은 없다. `notice`/`Notice` 를 자신의 `{domain}`/`{Domain}` 으로 바꿔 읽는다.

`features/{domain}/models/` 는 **ACL(Anti-Corruption Layer)·Adapter 계층** — 서버 DTO 를 Zod 로 묘사하고, Mapper 로 화면 모델(`types/` 의 `I{Domain}`)로 바꾼다.
백엔드 응답 형태가 바뀌어도 **이 폴더만 고치면** 상위 계층(services 이상)은 영향받지 않게 하는 것이 목적이다.

```
features/{domain}/models/
├── {domain}Schema.ts          # 서버 요청·응답 DTO Zod 스키마 (백엔드 그대로) + z.infer 타입
├── {domain}Mapper.ts          # DTO ↔ 화면 모델 변환 (class {Domain}Mapper, static 메서드)
├── {domain}Mock.ts            # (선택) 퍼블리싱 목데이터 — satisfies I{Domain}, API 전환 완료 시 제거
└── __tests__/{domain}Mapper.test.ts
```

> 파일명·코드 안의 `{domain}`은 camelCase(예: `blogPost`), `{Domain}`은 PascalCase(예: `BlogPost`). 도메인 **폴더**명은 kebab-case(`features/blog-post/`) — `naming-convention.md` 「폴더·파일」.
> 화면 모델 타입(`I{Domain}`, `ICreate{Domain}Input` …)은 여기가 아니라 **`types/{domain}Type.ts`** 에 둔다 (`types-layer.md`).
> 공용 `src/models/` 는 여러 도메인이 공유하는 DTO 조각(예: 공통 페이지네이션 스키마)만 둔다. 특정 도메인 import 금지.
> 이 프로젝트 규칙이 전역 `~/.claude/rules/frontend/` 보다 우선한다.

---

## 의존 방향

전체 순서·store 예외는 `architecture.md` 「도메인 내부 의존 방향」 (단일 출처). 이 계층 기준:

- `models/` 는 **`types/`·`constants/`·`utils/`·`lib/` 만** import 한다. `services/` 이상 import 시 ESLint 에러.
- 폴더 안 방향: `{domain}Schema.ts` → `{domain}Mapper.ts` (Mapper 가 Schema 의 타입과 `../types/{domain}Type` 를 import). 역방향 금지.

---

## 핵심 원칙

1. **flat 구조** — `models/` 내부에 하위 폴더 만들지 않음 (`__tests__/` 제외).
2. **순수성** — axios·React·TanStack Query·Zustand 등 어떤 런타임도 import 하지 않는다. Zod(`{domain}Schema.ts` 에서만)와 타입만 쓴다.
3. **DTO 외부 노출 금지** — `T{Domain}Dto` 같은 DTO 타입은 `models/` 와 `services/` 안에서만 보인다. queries 이상은 `types/` 의 화면 모델만 사용.
4. **API DTO 검증은 `safeParse` 만 — `parse` 금지** — 이 폴더의 스키마는 services 에서 `safeParse` 로만 쓴다 (`parse` 는 throw 위치 추적이 어렵다). 호출 패턴은 `services-layer.md` 「핵심 원칙」 3·8·9. 폼 입력 검증(`utils/validation.ts` + react-hook-form)은 별개 규칙 — `zod-usage` 스킬.

---

## 파일 1. `{domain}Schema.ts` — 서버 DTO 스키마

**목표**: 백엔드가 보내는(받는) 데이터를 **1:1 그대로** Zod 로 묘사. 변형하지 않는다.

### 사전 작업 (필수)
- 작성 전 **반드시** `frontend/swagger/docs.md` 의 해당 도메인 섹션을 읽는다. 기억·추측으로 스키마 작성 금지.
- 섹션이 없으면 `backend/sync-api-docs` 스킬(`.claude/skills/backend/sync-api-docs/SKILL.md`)로 백엔드 구현 코드에서 문서를 생성한다. 백엔드 미구현이면 멈추고 사용자에게 알린다.
- 모든 엔드포인트의 request·response 형태, 인증 여부, 에러 코드, 날짜 형식, nullable / optional 을 확인한다.

### 규칙
- 백엔드가 `snake_case` 면 그대로 `snake_case` 유지 (`created_at`).
- 날짜는 ISO8601 문자열 그대로 — 백엔드가 타임존 없는 naive datetime 을 줄 수 있으면 `z.string().datetime({ offset: true, local: true })`.
- nullable / optional 백엔드와 동일하게.
- envelope(`{status, data}`)의 **`data` 내부만** 묘사한다 — envelope 벗기기는 services 의 `getEnvelopeData`.
- 요청 DTO(POST/PUT/PATCH body)도 여기 정의 (`Create{Domain}RequestDtoSchema` …).
- **interface 따로 만들지 말 것** — `z.infer<typeof Schema>` 로 타입 추론. 이름: 스키마 상수 `{Domain}DtoSchema`, 타입 `T{Domain}Dto`.

### 예시 (가상의 `notice` 기능 기준 — 실제 파일 없음)
```ts
// features/notice/models/noticeSchema.ts — 백엔드 응답/요청 1:1 묘사 (frontend/swagger/docs.md notice 섹션 기준)
import { z } from 'zod';

// 백엔드 datetime은 naive ISO8601(타임존 없음)일 수 있어 offset/local 모두 허용
const isoDatetime = z.string().datetime({ offset: true, local: true });

export const NoticeSummaryDtoSchema = z.object({
  id: z.number().int(),
  title: z.string(),
  application: z.string(),
  user: z.string(),
  hits: z.number().int().nonnegative(),
  created_at: isoDatetime,
});
export type TNoticeSummaryDto = z.infer<typeof NoticeSummaryDtoSchema>;

export const NoticeDtoSchema = NoticeSummaryDtoSchema.extend({
  content: z.string(),
  updated_at: isoDatetime,
});
export type TNoticeDto = z.infer<typeof NoticeDtoSchema>;

export const NoticeListResponseDtoSchema = z.object({
  results: z.array(NoticeSummaryDtoSchema),
  pagination: z.object({
    current_page: z.number().int(),
    num_pages: z.number().int(),
    page_size: z.number().int(),
    total_count: z.number().int().nonnegative(),
    has_previous: z.boolean(),
    has_next: z.boolean(),
  }),
});
export type TNoticeListResponseDto = z.infer<typeof NoticeListResponseDtoSchema>;

export const CreateNoticeRequestDtoSchema = z.object({
  title: z.string().min(1).max(255),
  content: z.string().min(1),
  application: z.string().min(1).max(50),
});
export type TCreateNoticeRequestDto = z.infer<typeof CreateNoticeRequestDtoSchema>;

export const UpdateNoticeRequestDtoSchema = CreateNoticeRequestDtoSchema.partial();
export type TUpdateNoticeRequestDto = z.infer<typeof UpdateNoticeRequestDtoSchema>;
```

---

## 파일 2. `{domain}Mapper.ts` — DTO ↔ 화면 모델 변환

**목표**: DTO ↔ 화면 모델(`types/{domain}Type.ts`) 변환. **순수 함수, 부수효과 없음.**

### 규칙
- `export class {Domain}Mapper` + `static` 메서드 (인스턴스화 안 함, DI 없음). 메서드 이름은 `to{Target}` — Mapper 관행으로 `convert` 접두사의 예외 (`naming-convention.md` 「함수」). 파일명은 camelCase `{domain}Mapper.ts`, export 이름은 PascalCase `{Domain}Mapper`.
- `toDomain(dto)` — 단건 응답 변환 (필수). 목록 아이템이 축소형이면 `toSummary(dto)`.
- `toDomainList(dto)` — 목록·페이지네이션 응답이 있으면 추가.
- `toCreateDto(input)` / `toUpdateDto(input)` / `to{Action}Dto(...)` — 요청 변환 (보낼 body 가 있을 때만).
- 변환 내용: `snake_case` → `camelCase`, ISO 문자열 → `Date`, `null` → `undefined`, 필드 rename(`user` → `author`, `hits` → `viewCount`) 등.
- 비즈니스 로직(계산·분기·fetch) 금지 — 순수 매핑만.
- **services 외 다른 곳에서 호출 금지.**
- static 메서드 안에서 다른 static 을 부를 땐 **클래스명으로 호출** (`dto.results.map({Domain}Mapper.toSummary)`) — `this` 바인딩이 떨어진다.

### 예시 (가상의 `notice` 기능 기준 — 실제 파일 없음)
```ts
// features/notice/models/noticeMapper.ts — DTO ↔ Domain 변환 (순수 함수)
import type {
  TCreateNoticeRequestDto,
  TNoticeDto,
  TNoticeListResponseDto,
  TNoticeSummaryDto,
} from './noticeSchema';
import type {
  ICreateNoticeInput,
  INotice,
  INoticePage,
  INoticeSummary,
} from '../types/noticeType';

export class NoticeMapper {
  /** 목록 아이템 DTO → INoticeSummary (user→author, hits→viewCount rename) */
  static toSummary(dto: TNoticeSummaryDto): INoticeSummary {
    return {
      id: dto.id,
      title: dto.title,
      application: dto.application,
      author: dto.user,
      viewCount: dto.hits,
      createdAt: new Date(dto.created_at),
    };
  }

  /** 상세 DTO → INotice */
  static toDomain(dto: TNoticeDto): INotice {
    return {
      ...NoticeMapper.toSummary(dto), // static은 클래스명으로 호출 (this 바인딩 없음)
      content: dto.content,
      updatedAt: new Date(dto.updated_at),
    };
  }

  /** 목록 응답 DTO → INoticePage (표준 페이지네이션) */
  static toDomainList(dto: TNoticeListResponseDto): INoticePage {
    return {
      itemList: dto.results.map(NoticeMapper.toSummary),
      currentPage: dto.pagination.current_page,
      numPages: dto.pagination.num_pages,
      pageSize: dto.pagination.page_size,
      totalCount: dto.pagination.total_count,
      hasPrevious: dto.pagination.has_previous,
      hasNext: dto.pagination.has_next,
    };
  }

  /** 생성 입력 → 요청 DTO */
  static toCreateDto(input: ICreateNoticeInput): TCreateNoticeRequestDto {
    return { title: input.title, content: input.content, application: input.application };
  }
}
```

---

## 작성 순서 (권장)

1. **`frontend/swagger/docs.md`** 읽기 — 해당 도메인 섹션 확인 (없으면 `backend/sync-api-docs` 스킬).
2. **`types/{domain}Type.ts`** — 화면이 쓰기 좋은 모델 설계 (`types-layer.md`).
3. **`models/{domain}Schema.ts`** — 서버 형태 그대로 묘사.
4. **`models/{domain}Mapper.ts`** — 2 ↔ 3 변환 채우기.
5. **테스트** — 아래 「테스트 코드」.

> `services/{domain}Service.ts` 는 이 파일들 + 테스트가 갖춰진 뒤 작성한다 (`services-layer.md`).

---

## 테스트 코드

### 파일 위치
```
features/{domain}/models/__tests__/
├── {domain}Mapper.test.ts
└── {domain}Schema.test.ts     # (선택) 스키마 edge case 가 많을 때만
```

### 무엇을 테스트하는가
- **Mapper 변환**: `toDomain`·`toSummary` 가 `snake_case → camelCase`, `string → Date`, 필드 rename, `null → undefined` 를 정확히 수행하는가.
- **목록 매핑**: `toDomainList` 가 빈 배열(`itemList: []`)·페이지네이션 필드를 올바르게 옮기는가.
- **요청 변환**: `toCreateDto`·`toUpdateDto` 가 입력 필드를 누락 없이, 부분 수정은 전달된 필드만 매핑하는가.
- **DTO 스키마 `safeParse`**: 정상 응답 `success: true`, 타입 불일치·필수 필드 누락 `success: false`.

### 무엇을 테스트하지 않는가
- axios 호출 — services 테스트(MSW)에서 검증.
- React 렌더링 — 컴포넌트 테스트에서 검증.

### 템플릿
```ts
// features/{domain}/models/__tests__/{domain}Mapper.test.ts
import { describe, expect, it } from 'vitest';

import { {Domain}Mapper } from '../{domain}Mapper';
import { {Domain}DtoSchema, type T{Domain}Dto } from '../{domain}Schema';

const validDto: T{Domain}Dto = {
  id: 1,
  title: 'Hello',
  created_at: '2026-01-01T00:00:00Z',
  // ...
};

describe('{Domain}Mapper.toDomain', () => {
  it('snake_case → camelCase, 문자열 → Date 변환', () => {
    const model = {Domain}Mapper.toDomain(validDto);
    expect(model.createdAt).toBeInstanceOf(Date);
  });
});

describe('{Domain}DtoSchema.safeParse', () => {
  it('유효한 응답은 success: true', () => {
    expect({Domain}DtoSchema.safeParse(validDto).success).toBe(true);
  });

  it('필수 필드 누락 시 success: false', () => {
    const { title: _title, ...broken } = validDto;
    expect({Domain}DtoSchema.safeParse(broken).success).toBe(false);
  });
});
```

> `pnpm test src/features/{domain}/models` 로 이 계층 테스트만 빠르게 실행.

---

## 체크리스트

- [ ] `frontend/swagger/docs.md` 의 해당 도메인 섹션을 실제로 읽었는가?
- [ ] `models/` 에 `{domain}Schema.ts`·`{domain}Mapper.ts`(+ 선택 `{domain}Mock.ts`, `__tests__/`)만 존재?
- [ ] 스키마는 백엔드 형태를 변형 없이 묘사? (snake_case 유지, envelope 의 `data` 내부만)
- [ ] 타입은 `z.infer` + `T` 접두사(`T{Domain}Dto`)? 별도 interface 없음?
- [ ] 화면 모델 타입은 `types/{domain}Type.ts` 에서 import? (models 에 `I{Domain}` 정의 없음)
- [ ] 이 스키마의 API 검증은 `safeParse` 만? (`parse` 0건 — 폼 검증은 `zod-usage` 스킬)
- [ ] Mapper 는 `class {Domain}Mapper` + `static` 메서드, static 끼리 클래스명 호출?
- [ ] Mapper 에 fetch·계산·분기 같은 비즈니스 로직 없음?
- [ ] axios·React·TanStack Query·Zustand import 없음? `services/` 이상 import 없음?
- [ ] Mapper 테스트(정상 + edge case) + 스키마 `safeParse` 테스트?
- [ ] `pnpm test src/features/{domain}/models` 통과?

## 금지 사항

- ❌ `models/` 에서 `services/`·`queries/`·`hooks/`·`components/` import (의존 방향 위반 — ESLint 에러)
- ❌ API DTO 검증에 `parse()` 사용 / 스키마로 백엔드 응답을 가공(transform)해 형태를 바꾸기
- ❌ DTO 타입(`T{Domain}Dto`)을 services 밖으로 노출
- ❌ 다른 도메인의 `models/` 직접 import (도메인 간 규칙은 `architecture.md`)
