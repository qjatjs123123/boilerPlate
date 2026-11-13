---
description: backend/app/domains/{domain}/service.py — 비즈니스 로직 계층 작성 또는 수정 시
paths:
  - "backend/app/domains/*/service.py"
---

# Service Layer — 비즈니스 로직 규칙

`app/domains/{domain}/service.py` 는 **비즈니스 로직 전담** 계층. 유스케이스를 구현하고 트랜잭션 경계를 소유한다.
공통 코딩 규칙(네이밍·포맷팅·import·주석)은 `python-convention.md` — 기준은 `docs/backend/CONVENTIONS.md`.

---

## 네이밍

- 클래스: `{Entity}Service` — `PostService`.
- 공개 메서드 = **유스케이스명** (동사+명사) — `get_post`, `get_post_page`, `create_post`, `update_post`, `delete_post`, `like_post`.
- 비공개 헬퍼는 `_` 접두사 + 의도가 드러나는 동사 — `_ensure_author`, `_generate_slug`, `_calculate_score`.
- 주입 속성은 약어 없이 — `self.repository`, 다른 도메인이면 `self.user_repository` (`self.repo` ❌).
- 로그 이벤트명은 `{domain}_{과거형 동사}` snake_case — `"post_created"`, `"post_liked"`.

## 핵심 원칙

1. **메서드 1개 = 유스케이스 1개**, 20줄 초과 시 `_` 헬퍼로 분리.
2. **클래스 + 생성자 주입** — `def __init__(self, db: Session, repository: PostRepository) -> None`. 조립은 라우터 deps 함수.
3. **`HTTPException` 금지** — `domains/{domain}/exceptions.py` 의 `AppException` 서브클래스만 raise.
4. **트랜잭션 경계 소유** — 쓰기 유스케이스 마지막에 `self.db.commit()`. repository 는 flush 까지.
5. **존재·권한 검증은 service** — 반복되는 검증은 `get_post()` / `_ensure_author()` 같은 헬퍼 하나로 모은다(코드 반복 최소화).
6. **비정규화 카운터 갱신은 service** — 같은 트랜잭션 안에서.
7. **다른 도메인이 필요하면 그 도메인의 repository 를 추가 주입** — service → service 호출 금지.
8. **반환은 엔티티 or 도메인 결과(`Page` 등)** — Response 스키마 변환·envelope 조립은 router.
9. **주요 상태 변화는 `log_event(...)`** (`app/common/logging.py`). `print` 금지.
10. 가드 먼저(early return / raise), 본문은 정상 흐름만. Boolean 비교는 `if not post.is_published:` 형태.
11. 매직 값(기본 정렬, 최대 개수 등)은 모듈 상단 상수.

## 템플릿

> 아래 `Post` 는 규칙을 보여 주기 위한 **설명용 예시**다 (`slug`·`tags`·`like_count` 등 실제 테이블에 없는 필드 포함). 실제 컬럼은 `backend/data-model.yaml` 이 단일 출처이고, 구현 예는 `backend/app/domains/post/` 를 본다.

```python
# app/domains/post/service.py
from sqlalchemy.orm import Session

from app.common.logging import log_event
from app.common.pagination import Page, PageParams
from app.domains.post.exceptions import PostForbiddenException, PostNotFoundException, PostSlugDuplicateException
from app.domains.post.models import Post
from app.domains.post.repository import PostRepository
from app.domains.post.schemas import PostCreateRequest, PostUpdateRequest
from app.domains.user.models import User


class PostService:
    """포스트 유스케이스 전담"""

    def __init__(self, db: Session, repository: PostRepository) -> None:
        self.db = db
        self.repository = repository

    def get_post(self, post_id: int) -> Post:
        """단건 조회 — 없으면 PostNotFoundException"""
        post = self.repository.find_by_id(post_id)
        if post is None:
            raise PostNotFoundException()
        return post

    def get_post_page(self, page_params: PageParams) -> Page[Post]:
        """발행된 포스트 페이지 조회"""
        posts = self.repository.find_all_published(page_params.page_size, page_params.offset)
        total_count = self.repository.count_published()
        return Page(
            items=posts,
            total_count=total_count,
            current_page=page_params.page,
            page_size=page_params.page_size,
        )

    def create_post(self, author: User, request: PostCreateRequest) -> Post:
        """생성 — 슬러그는 제목 기반 자동 발급"""
        slug = self._generate_slug(request.title)
        post = Post(author_id=author.id, slug=slug, **request.model_dump(exclude={"tags"}))
        saved_post = self.repository.save(post)
        self.db.commit()
        log_event("post_created", post_id=saved_post.id, author_id=author.id)
        return saved_post

    def update_post(self, post_id: int, user: User, request: PostUpdateRequest) -> Post:
        """부분 수정 — 작성자 본인만"""
        post = self.get_post(post_id)
        self._ensure_author(post, user)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(post, field, value)
        saved_post = self.repository.save(post)
        self.db.commit()
        return saved_post

    def _ensure_author(self, post: Post, user: User) -> None:
        """작성자가 아니면 PostForbiddenException"""
        if post.author_id != user.id:
            raise PostForbiddenException()

    def _generate_slug(self, title: str) -> str:
        """제목으로 슬러그 생성 — 이미 있으면 PostSlugDuplicateException"""
        slug = title.strip().lower().replace(" ", "-")
        if self.repository.exists_by_slug(slug):
            raise PostSlugDuplicateException()
        return slug
```

## 테스트

- 위치: `tests/unit/domains/{domain}/test_service.py`
- repository·db 를 **`Mock(spec=...)`** 로 주입한 순수 단위 테스트 (DB 없음).
- 검증: ① 올바른 repository 메서드·인자 호출 ② 없는 리소스 → 도메인 예외 ③ 권한 없음 → 도메인 예외 ④ 쓰기 성공 시 `db.commit()` 호출.

```python
def test_get_post_when_missing_raises_not_found() -> None:
    """존재하지 않는 포스트 조회 시 PostNotFoundException"""
    repository = Mock(spec=PostRepository)
    repository.find_by_id.return_value = None
    service = PostService(db=Mock(spec=Session), repository=repository)

    with pytest.raises(PostNotFoundException):
        service.get_post(MISSING_POST_ID)
```

---

## 체크리스트

- [ ] 공개 메서드명 = 유스케이스명, 헬퍼는 `_` 접두사?
- [ ] 속성·변수명 약어 없음 (`self.repository`, `saved_post`)?
- [ ] `HTTPException` 0건?
- [ ] 쓰기 유스케이스 끝에 `self.db.commit()`?
- [ ] 존재·권한 검증이 헬퍼로 모여 있음 (중복 없음)?
- [ ] 메서드 20줄 이내?
- [ ] Response 스키마·envelope 조립 없음?
- [ ] 다른 도메인은 repository 주입으로만?
- [ ] `pytest tests/unit/domains/{domain}/test_service.py` 통과?

## 금지 사항

- ❌ `HTTPException` raise, FastAPI import (`Depends`, `Request` …)
- ❌ `select()` 등 쿼리 직접 작성 (repository 로)
- ❌ 다른 도메인 service 호출
- ❌ 같은 존재·권한 검증 코드를 메서드마다 복붙
- ❌ `print`, 예외 삼키기 (`except Exception: pass`)
- ❌ 커밋 전 상태를 응답에 노출
