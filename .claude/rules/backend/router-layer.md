---
description: backend/app/domains/{domain}/router.py — Controller(라우터) 계층 작성 또는 수정 시
paths:
  - "backend/app/domains/*/router.py"
---

# Router Layer — Controller 규칙

`app/domains/{domain}/router.py` 는 **HTTP 입출력 전담** 계층 — 파라미터 바인딩, service 호출, 스키마 변환, envelope 반환. 그 이상은 하지 않는다.
공통 코딩 규칙(네이밍·포맷팅·import·주석)은 `python-convention.md` — 기준은 `docs/backend/CONVENTIONS.md`.

---

## 네이밍

- 라우터 객체: `router = APIRouter(prefix="/api/{리소스 복수형}", tags=["{리소스 복수형}"])`.
- deps 함수: `get_{domain}_service` — `get_post_service`.
- 엔드포인트 함수 = **유스케이스명** (service 메서드와 동일) — `get_post`, `get_post_page`, `create_post`. FastAPI operation_id 로도 쓰인다.
- 인자명 약어 없이 — `service`, `request`, `current_user`, `page_params` (`svc`, `req`, `user_id_` ❌).
- URL 경로: 리소스 복수형 kebab-case — `/api/posts`, `/api/post-series/{series_id}`.
- 경로 파라미터: `snake_case` — `{post_id}`.
- 쿼리 파라미터: **kebab-case alias** — `Query(alias="page-size")`, `Query(alias="search-keyword")`. Python 변수명은 `snake_case`.

## 핵심 원칙

1. **thin controller — 엔드포인트 함수 10줄 내외.** 바인딩 → service 호출 → 스키마 변환 → envelope. 분기는 service 로.
2. **DI 체인은 deps 함수로** — `get_db → {Domain}Repository → {Domain}Service`. 엔드포인트에서 직접 인스턴스화 금지. 다른 도메인 repository 가 필요하면 deps 함수에서 함께 생성해 주입한다 (`PostService(db=db, repository=PostRepository(db), user_repository=UserRepository(db))`) — 한 요청의 모든 레이어가 같은 세션 하나를 공유한다.
3. **`Annotated` 스타일** — `service: Annotated[PostService, Depends(get_post_service)]`. 같은 Annotated 가 3번 이상 반복되면 모듈 상단 타입 별칭으로(`PostServiceDep`).
4. **try/except 금지** — 예외 → envelope 는 글로벌 핸들러 담당.
5. **DB 직접 접근 금지** — `Session` 은 엔드포인트 시그니처에 없다. deps 함수 안에만.
6. **응답은 envelope** — `success_response(...)` (`app/common/response.py`). 목록은 `paginate()`/`cursor_page()` 결과를 data 로. 생성은 `status_code=201`.
7. **엔티티는 반환 직전 Response 스키마로** — `PostResponse.model_validate(post)`.
8. 인증 `Depends(get_current_user)` / 선택 인증 `get_current_user_optional`. 인증된 User 는 엔드포인트가 받아 service 메서드 인자로 넘긴다. 권한 판정 자체는 service.
9. HTTP 메서드: 조회 `GET`, 생성 `POST`, 부분 수정 `PATCH`, 전체 교체 `PUT`, 삭제 `DELETE`.
10. 상태 코드 등 매직 넘버는 `fastapi.status` 상수 허용 — `status_code=status.HTTP_201_CREATED`.

## 템플릿

```python
# app/domains/post/router.py
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.pagination import PageParams, paginate
from app.common.response import SuccessResponse, success_response
from app.core.security import get_current_user
from app.db.deps import get_db
from app.domains.post.repository import PostRepository
from app.domains.post.schemas import PostCreateRequest, PostResponse, PostSummaryResponse
from app.domains.post.service import PostService
from app.domains.user.models import User

router = APIRouter(prefix="/api/posts", tags=["posts"])


def get_post_service(db: Annotated[Session, Depends(get_db)]) -> PostService:
    """PostService 조립 (get_db → Repository → Service)"""
    return PostService(db=db, repository=PostRepository(db))


PostServiceDep = Annotated[PostService, Depends(get_post_service)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.get("/{post_id}")
def get_post(post_id: int, service: PostServiceDep) -> SuccessResponse[PostResponse]:
    """포스트 단건 조회"""
    post = service.get_post(post_id)
    return success_response(PostResponse.model_validate(post))


@router.get("")
def get_post_page(
    service: PostServiceDep,
    page_params: Annotated[PageParams, Depends()],
) -> SuccessResponse[dict[str, object]]:
    """포스트 목록 조회 (페이지 번호) — 검색어 등 추가 쿼리는 Query(alias="search-keyword") 로 받아 service 인자로 넘긴다"""
    page = service.get_post_page(page_params)
    return success_response(paginate(page, PostSummaryResponse))


@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(
    request: PostCreateRequest,
    service: PostServiceDep,
    current_user: CurrentUserDep,
) -> SuccessResponse[PostResponse]:
    """포스트 생성"""
    post = service.create_post(current_user, request)
    return success_response(PostResponse.model_validate(post))
```

> `get_current_user` 위치는 프로젝트 인증 구현을 따른다(`app/core/security.py`). 새 라우터는 `app/main.py` 에 `app.include_router(router)` 로 등록한다.

## 응답 envelope

형식의 원본은 `exception-handling.md` 「응답 envelope 스펙」 (목록 형태 선택은 `api-spec` 스킬). 라우터는 `success_response`·`paginate()`·`cursor_page()` 로만 조립하고, 실패 응답은 만들지 않는다 — 도메인 예외 → 글로벌 핸들러.

## 테스트

- 위치: `tests/api/test_{domain}.py` — `TestClient` + `app.dependency_overrides` 로 service mock (DB 없음).
- override 키는 **deps 함수 자체**(`app.dependency_overrides[get_post_service]`) — 내부의 `get_db` 가 아니다.
- 검증: ① status code ② envelope 구조 ③ service 호출 인자 ④ 도메인 예외 시 fail envelope.
- 상세 템플릿은 `test-convention.md`.

---

## 체크리스트

- [ ] 함수명 = 유스케이스명, 인자명 약어 없음?
- [ ] 엔드포인트 10줄 내외, 분기 없음?
- [ ] try/except 0건, `Session` 시그니처 노출 0건?
- [ ] 쿼리 파라미터 kebab-case alias, 경로 파라미터 snake_case?
- [ ] 응답 전부 `success_response` 경유 + Response 스키마 변환?
- [ ] deps 함수로 service 조립, 반복 Annotated 는 별칭?
- [ ] `pytest tests/api/test_{domain}.py` 통과?

## 금지 사항

- ❌ `select()`·`db.query()`·`db.execute()` 등 쿼리 직접 실행
- ❌ `HTTPException` raise, try/except 로 에러 응답 조립
- ❌ envelope 없이 스키마·dict·엔티티 반환
- ❌ 권한 분기 로직 (service 로)
- ❌ camelCase·snake_case 쿼리 파라미터 alias
- ❌ 엔드포인트 안에서 `PostService(...)` 직접 생성
- ❌ 모듈 전역에서 세션·repository·service 인스턴스 생성 (요청 간 상태 공유 버그)
- ❌ service/repository 에 `Depends` 사용 — FastAPI 의존은 라우터 계층까지만
- ❌ 구식 기본값 스타일 `service: PostService = Depends(...)` — `Annotated` 로 통일 (ruff `B008` 이 차단)
