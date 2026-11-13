---
description: JS/TS 함수 작성 시
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---

# JS 함수 규칙

> **이 프로젝트 전용 (사내 FE 컨벤션 반영)** — 전역 `~/.claude/rules/frontend/javascript-convention.md` 와 다르면 이 파일이 우선한다.

- 함수 15줄 이내, 단일 책임 — 일반 함수·훅·service 메서드 기준. **React 컴포넌트는 줄 수가 아니라 「책임 한 문장」 기준** (`react-convention.md` 「적절한 길이 유지」)
- 이름은 `naming-convention.md` (camelCase 동사+명사, 상수 UPPER_SNAKE_CASE)
- export 하는 함수 위에는 JSDoc 한 줄 설명 — 공용 코드는 필수 (아래 「주석」)
- 인자 3개 초과 시 객체로
- early return으로 중첩 축소
- 순수 함수 지향, 부수효과 최소

## 유틸·헬퍼 위치 (사내 FE 아키텍처)

- **도메인 무관 순수 함수** → 공용 `src/utils/{name}.ts` (예: `utils/formatDate.ts` 의 `formatDateDot`, `utils/errors.ts`). 특정 도메인(`features/`) import 금지.
- **한 도메인 전용 순수 함수** → `features/{domain}/utils/{name}.ts`. 외부 라이브러리 래퍼는 `lib/` (공용 `src/lib/` 또는 도메인 `lib/`).
- `utils/`·`lib/` 는 도메인 의존 방향의 최하단(`architecture.md` 「도메인 내부 의존 방향」) — **상위 계층(models·services·queries·hooks·components) import 금지** (`architecture.md`).
- 상수는 `utils/` 가 아니라 `constants/{name}Constants.ts` (`types-layer.md`).
- 한 파일에서만 쓰는 헬퍼는 그 파일 하단의 모듈 함수로 둔다 (예: `{domain}Service.ts` 의 `requestBody`, `getEnvelopeData`, `toDataLayerError`).

## 주석 (사내 컨벤션)

- **공용으로 쓰일 코드(훅·util·공용 컴포넌트·lib)는 주석 필수** — 무엇을 위한 것인지 JSDoc 한 줄 이상. 도메인 전용 코드는 export 함수에 JSDoc 한 줄(권장).
- 주석은 "왜"를 쓴다. 코드로 드러나는 "무엇"은 반복하지 않는다.
- 형식 — JSDoc·`//` 주석 공통. `[영역]` 표기는 한 파일에 여러 영역이 섞여 구분이 필요할 때 붙인다 (선택):
  ```ts
  // TODO: api 연동 이후 mockdata 삭제          ← 남은 작업은 TODO: + 할 일
  // [테이블] 행 선택 상태를 페이지 이동 시 초기화하기 위한 함수   ← [영역] + 목적
  /** [공지 목록] 페이지 조회 queryKey·queryFn */   ← JSDoc 도 같은 형식
  ```
- `TODO` 에는 무엇을 하면 지울 수 있는지까지 적는다.
