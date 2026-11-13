---
description: backend/app/domains/{domain}/repository.py — DB 접근 계층 작성 또는 수정 시
paths:
  - "backend/app/domains/*/repository.py"
---

# Repository Layer — DB 접근 규칙

`app/domains/{domain}/repository.py` 는 **DB 접근 전담** 계층. 쿼리만 알고, 비즈니스는 모른다.
공통 코딩 규칙(네이밍·포맷팅·import·주석)은 `python-convention.md` — 기준은 `docs/backend/CONVENTIONS.md`.

---

## 네이밍

- 클래스: `{Entity}Repository` (`PascalCase`) — `PostRepository`.
- 메서드 (`snake_case` 동사+명사)

| 용도 | 이름 | 반환 |
|---|---|---|
| 단건 조회 | `find_by_{field}` | `Entity \| None` |
| 목록 조회 | `find_all_by_{field}` / `find_all_{조건}` | `Sequence[Entity]` |
| 개수 | `count_by_{field}` / `count_{조건}` | `int` |
| 존재 여부 | `exists_by_{field}` | `bool` |
| 저장 (INSERT/UPDATE) | `save` | `Entity` |
| 삭제 | `delete` | `None` |

- 지역 변수도 약어 없이 — 쿼리 객체는 `statement` (`stmt` ❌), 결과는 의미 있는 이름(`posts`, `post_count`).
- 세션 속성은 프로젝트 표준인 `self.db`.

## 핵심 원칙

1. **DB 접근만** — 비즈니스 분기·권한 체크·카운터 계산 금지.
2. **raise 금지** — 없으면 `None` / 빈 시퀀스. 404 판단은 service.
3. **클래스 + `Session` 생성자 주입** — `def __init__(self, db: Session) -> None`. 모듈 전역 세션 금지.
4. **쿼리는 SQLAlchemy 2.0 스타일만** (모델 선언은 `model-layer.md` 의 `Column` 방식 그대로) — `select()` + `self.db.scalars()` / `self.db.scalar()` / `self.db.execute()`. PK 단건은 `self.db.get(Model, id)`. **`db.query()` 금지.**
5. **`commit()`·`rollback()` 금지 — `flush()` 까지만.** 트랜잭션은 service 소유.
6. **N+1 방지** — 상위 계층이 접근할 관계는 쿼리에 eager load 를 명시한다 (lazy load 에 기대면 세션 밖 접근 시 `DetachedInstanceError`). 루프 안에서 쿼리 호출 금지 — 루프 밖에서 IN 조건으로 일괄 조회.

   | 관계 | 옵션 | 이유 |
   |---|---|---|
   | 컬렉션 (`Post.tags`, `Post.comments`) | `selectinload` | IN 쿼리 1개 추가 — 행 폭발 없음 |
   | 단일 (`Post.author`) | `joinedload` | JOIN 1번 — 추가 왕복 없음 |
7. **반환은 엔티티·기본형** — Pydantic 스키마·dict 반환 금지.
8. **Boolean·None 조건은 `.is_()` / `.is_not()`** — `Post.is_published.is_(True)`, `Post.deleted_at.is_(None)`. `== True` / `== None` 금지.
9. **반복되는 eager load 옵션은 `_` 비공개 헬퍼나 모듈 상수로** 한 번만 정의 — 코드 반복 최소화.
10. SQL 은 ORM 파라미터 바인딩만. f-string SQL 금지, `text()` 는 불가피할 때만 + 바인딩 파라미터.

## 템플릿

> 아래 `Post` 는 규칙을 보여 주기 위한 **설명용 예시**다 (`slug`·`tags`·`like_count` 등 실제 테이블에 없는 필드 포함). 실제 컬럼은 `backend/data-model.yaml` 이 단일 출처이고, 구현 예는 `backend/app/domains/post/` 를 본다.

```python
# app/domains/post/repository.py
from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.domains.post.models import Post


class PostRepository:
    """포스트 DB 접근 전담"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _select_with_relations(self) -> Select[tuple[Post]]:
        """작성자·태그를 함께 읽는 기본 select — 상위 계층의 lazy load 방지"""
        return select(Post).options(joinedload(Post.author), selectinload(Post.tags))

    def find_by_id(self, post_id: int) -> Post | None:
        """ID로 단건 조회 (관계 eager load)"""
        statement = self._select_with_relations().where(Post.id == post_id)
        return self.db.scalars(statement).first()

    def find_all_published(self, limit: int, offset: int) -> Sequence[Post]:
        """발행된 포스트 최신순"""
        statement = (
            self._select_with_relations()
            .where(Post.is_published.is_(True))
            .order_by(Post.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return self.db.scalars(statement).all()

    def count_published(self) -> int:
        """발행된 포스트 수"""
        statement = select(func.count()).select_from(Post).where(Post.is_published.is_(True))
        return self.db.scalar(statement) or 0

    def exists_by_slug(self, slug: str) -> bool:
        """슬러그 중복 여부"""
        statement = select(Post.id).where(Post.slug == slug).limit(1)
        return self.db.scalars(statement).first() is not None

    def save(self, post: Post) -> Post:
        """INSERT/UPDATE 공용 — commit 은 service 책임"""
        self.db.add(post)
        self.db.flush()
        return post

    def delete(self, post: Post) -> None:
        """삭제 — commit 은 service 책임"""
        self.db.delete(post)
        self.db.flush()
```

## 쿼리 패턴

```python
from sqlalchemy import and_, func, or_, select, update

# 집계 + 그룹 — 튜플 행은 scalars 가 아니라 execute
statement = (
    select(Tag, func.count(post_tag.c.post_id).label("post_count"))
    .outerjoin(post_tag)
    .group_by(Tag.id)
    .order_by(func.count(post_tag.c.post_id).desc())
    .limit(POPULAR_TAG_LIMIT)
)
rows = self.db.execute(statement).all()

# 카운터 증가는 원자적으로 — read-modify-write 경합 방지 (증가 여부 결정은 service)
def increment_view_count(self, post_id: int) -> None:
    """조회수 1 증가"""
    statement = update(Post).where(Post.id == post_id).values(view_count=Post.view_count + 1)
    self.db.execute(statement)

# 커서 페이지네이션 (피드 전용) — (정렬키, id) 복합 커서로 중복·누락 방지
def find_all_published_after(self, cursor: PostCursor | None, limit: int) -> Sequence[Post]:
    """커서 이후 발행 포스트 — limit + 1 개를 읽어 다음 페이지 유무를 판정한다"""
    statement = self._select_with_relations().where(Post.is_published.is_(True))
    if cursor is not None:
        statement = statement.where(
            or_(
                Post.published_at < cursor.published_at,
                and_(Post.published_at == cursor.published_at, Post.id < cursor.id),
            )
        )
    statement = statement.order_by(Post.published_at.desc(), Post.id.desc()).limit(limit + 1)
    return self.db.scalars(statement).all()
```

- 커서 결과는 service 가 `has_next = len(posts) > limit`, `posts[:limit]` 로 자르고, envelope 조립은 router 가 `app/common/pagination.py` 의 `cursor_page()` 로 한다.

## 테스트

- 위치: `tests/unit/domains/{domain}/test_repository.py` — conftest 의 `db_session` 으로 실제 쿼리 검증.
- 검증: ① 조건에 맞는 행만 반환 ② 없으면 `None`/빈 시퀀스 ③ 정렬·페이지 ④ `save`/`delete` 후 조회 결과.

```python
def test_find_by_id_when_missing_returns_none(db_session: Session) -> None:
    """존재하지 않는 ID는 None을 반환한다"""
    repository = PostRepository(db_session)

    assert repository.find_by_id(MISSING_POST_ID) is None
```

---

## 체크리스트

- [ ] 메서드명이 `find_by_*`/`find_all_*`/`count_*`/`exists_by_*`/`save`/`delete`?
- [ ] `db.query()` 0건, `commit()`/`rollback()` 0건?
- [ ] raise 0건?
- [ ] 관계 조회에 `selectinload`/`joinedload` 명시, 옵션 중복 없음?
- [ ] Boolean·None 조건이 `.is_()` / `.is_not()`?
- [ ] 변수명 약어 없음 (`statement`, `repository`)?
- [ ] `pytest tests/unit/domains/{domain}/test_repository.py` 통과?

## 금지 사항

- ❌ `HTTPException`·도메인 예외 raise
- ❌ `db.commit()` / `db.rollback()` / `db.query()`
- ❌ 비즈니스 분기 (권한, 카운터 계산)
- ❌ Pydantic 스키마 import, 다른 도메인 repository 호출
- ❌ `Post.is_published == True`, `stmt`·`repo` 같은 약어
- ❌ f-string SQL
- ❌ 루프 안 쿼리 (N+1)
- ❌ 피드 무한스크롤에 offset 사용 — 커서로
