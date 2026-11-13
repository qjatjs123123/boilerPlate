# Architecture Layers

규칙 본문의 단일 출처는 `.claude/rules/**` 이다. 이 문서는 **계층 지도 + 강제 방식 + 위반 수정법**만 담는다.

## Backend — `backend/app/domains/{domain}/`

```
router.py      HTTP 입출력 (thin)          ─┐
service.py     유스케이스 + 트랜잭션 경계    │ 의존 방향 ↓ 만
repository.py  DB 접근 (select, flush)     │
models.py      SQLAlchemy 엔티티            ─┘
schemas.py     Pydantic DTO (router·service 경계)    exceptions.py  도메인 예외
```

| 규칙 ID (경계 테스트) | 금지 | 규칙 문서 |
|---|---|---|
| `no-http-exception` | 모든 레이어 `HTTPException` | `rules/backend/exception-handling.md` |
| `service-no-fastapi` / `service-no-query` | service 의 fastapi import, `select` 작성 | `rules/backend/service-layer.md` |
| `service-no-cross-service` | 다른 도메인 service import | `rules/backend/service-layer.md` |
| `repository-no-schema` / `-no-fastapi` | repository 의 스키마·fastapi import | `rules/backend/repository-layer.md` |
| `repository-no-commit-or-legacy` | repository 의 `.commit()` `.rollback()` `.query()` | `rules/backend/repository-layer.md` |
| `router-no-query` / `router-no-db` | router 의 `select`, `db.execute/scalars/query/commit` | `rules/backend/router-layer.md` |
| `models-no-cross-import` / `-no-framework` | 다른 도메인 모델 클래스 import, pydantic·fastapi import | `rules/backend/model-layer.md` |
| `schemas-no-db` | 스키마의 repository·service·Session 의존 | `rules/backend/schema-layer.md` |
| `common-no-domain` | `app/common` 의 도메인 import | `rules/backend/exception-handling.md` |

강제: `backend/tests/architecture/test_boundary.py` (pytest 에 포함 → `make check`, Stop 게이트, CI)

## Frontend — 사내 3계층 (`frontend/src/`)

Page `app/` (라우팅만) → Feature `features/{domain}/` → Shared `components/{ui,layout,shared}/`·`lib/`·`utils/` 등.

```
pages/       {X}Page — app/**/page.tsx 가 export   ─┐
components/  UI ({Name}/index.tsx)                 │
hooks/       useRead*(useQuery) · useMutation      │
store/       Zustand 도메인 상태                     │ 의존 방향 ↓ 만
queries/     queryKey + queryOptions               │
services/    axiosInstance + safeParse + Mapper    │
models/      Zod schema · Mapper                   │
types/ · constants/ · utils/ · lib/                ─┘
```

| 금지 | 규칙 문서 |
|---|---|
| 아래 계층이 위 계층 import (예: models → services) | `rules/frontend/{types,models,services,queries,store,hooks}-layer.md` |
| 공용 계층(`components/`·`hooks/`·`utils/` 등)이 `features/` import (공용 `hooks/` → `features/*/queries/` 는 허용) | `rules/frontend/architecture.md` |
| `app/` 이 `features/*/pages` 외의 폴더 import | `rules/frontend/architecture.md` |
| 다른 도메인 직접 import (`FEATURE_DEPENDENCIES` 미등록) | `rules/frontend/architecture.md` |
| services 밖에서 `@/lib/axios`·`axios` import | `rules/frontend/axios.md` |

강제: `frontend/eslint.config.mjs` (`import/no-restricted-paths`, `no-restricted-imports`) → `make check`, Stop 게이트, CI

## 위반을 만났을 때

1. 에러 메시지에 적힌 `.claude/rules/...` 문서를 읽는다.
2. 의존을 올바른 계층으로 옮긴다 (예: service 의 쿼리 → repository 메서드 추가 후 호출).
3. **규칙을 끄거나 `known-violations.json` 에 추가하지 않는다.** 기존 위반 목록은 고칠 때 삭제만 한다(래칫).
