---
description: backend/app/domains/{domain}/models.py — SQLAlchemy 엔티티 작성 또는 수정 시
paths:
  - "backend/app/domains/*/models.py"
---

# Model Layer — SQLAlchemy 엔티티 규칙

`app/domains/{domain}/models.py` 는 **DB 테이블 정의 전용** 계층. 4계층(`router → service → repository → models`)의 최하단.
공통 코딩 규칙(네이밍·포맷팅·import·주석)은 `python-convention.md` — 기준은 `docs/backend/CONVENTIONS.md`.
**테이블 설계·정규화는 `db-design.md`** — models.py 는 `backend/data-model.yaml` 과 똑같이 만든다 (`test_schema.py` 가 검사).

---

## 네이밍

| 대상 | 형식 | 예 |
|---|---|---|
| 모델 클래스 | `PascalCase` **단수형** | `Post`, `PostLike`, `User` |
| 테이블명 | `snake_case` **복수형** | `posts`, `post_likes`, `users` |
| 관계 테이블 | 단수 조합 허용 | `post_tag` |
| 컬럼 | `snake_case`, 약어 없이 | `author_id`, `published_at` (`pub_dt` ❌) |
| Boolean 컬럼 | `is_` / `has_` 접두사 | `is_staff`, `is_published` |
| unique 제약 | `uq_{테이블단수}_{컬럼}` | `uq_post_user_like` |
| 인덱스(명시 시) | `ix_{테이블}_{컬럼}` | `ix_posts_author_id` |

## 핵심 원칙

1. **컬럼·관계 정의만** — 비즈니스 로직·조회·계산 메서드 금지 (service/repository 책임).
2. **PK 는 integer autoincrement** — `id = Column(Integer, primary_key=True, autoincrement=True)`. 다른 레이어에서도 ID 타입은 `int`.
3. **`created_at`·`updated_at` 필수** (순수 관계 테이블은 생략 가능) — `default=datetime.utcnow` / `onupdate=datetime.utcnow`.
4. **FK 는 `ondelete` 명시** — `ForeignKey("users.id", ondelete="CASCADE")`.
5. **relationship 은 다른 도메인 모델을 문자열로 참조** — `relationship("User", ...)`. 다른 도메인 모델 클래스 import 금지(순환 방지).
6. **비정규화 카운터**(`like_count` 등)는 허용하되 `default=0`, `nullable=False`. 갱신은 service.
7. **association table 은 소유 도메인의 models.py** 에.
8. **unique 제약은 `__table_args__` 의 이름 붙은 `UniqueConstraint`**.
9. Boolean 컬럼은 `nullable=False` + 명시적 `default` — 3값(None) 상태를 만들지 않는다.
10. 매직 길이값은 상수로 — `TITLE_MAX_LENGTH = 255` 를 모듈 상단에 두고 `String(TITLE_MAX_LENGTH)`. 스키마의 `Field(max_length=...)` 와 같은 값을 쓴다.

## 컬럼 선언 순서

클래스 안은 아래 순서로, 그룹 사이에 빈 줄 1줄. 그룹 이름 주석은 달지 않는다(순서 자체가 규칙).

1. `__tablename__`, `__table_args__`
2. 식별자 — `id`
3. FK 컬럼 — `author_id`, ...
4. 일반 컬럼
5. 카운터 컬럼
6. 메타데이터 — `created_at`, `updated_at`
7. relationship

## 템플릿

> 아래 `Post` 는 규칙을 보여 주기 위한 **설명용 예시**다 (`slug`·`tags`·`like_count` 등 실제 테이블에 없는 필드 포함). 실제 컬럼은 `backend/data-model.yaml` 이 단일 출처이고, 구현 예는 `backend/app/domains/post/` 를 본다.

```python
# app/domains/post/models.py
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base

TITLE_MAX_LENGTH = 255
SLUG_MAX_LENGTH = 255


class Post(Base):
    """포스트 — slug 는 전역 unique"""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(TITLE_MAX_LENGTH), nullable=False)
    slug = Column(String(SLUG_MAX_LENGTH), nullable=False, unique=True)
    content = Column(Text, nullable=False)
    is_published = Column(Boolean, nullable=False, default=False)
    published_at = Column(DateTime, nullable=True)

    like_count = Column(Integer, nullable=False, default=0)  # 비정규화 캐시 — 갱신은 service

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", backref="posts")


class PostLike(Base):
    """포스트 좋아요 — 사용자당 1회"""

    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_user_like"),)

    id = Column(Integer, primary_key=True, autoincrement=True)

    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Alembic 워크플로 (모델 변경 시 필수)

1. 새 도메인 models.py 를 만들면 **`alembic/env.py` 에 import 추가** (autogenerate 메타데이터 등록).
2. `alembic revision --autogenerate -m "add_posts_table"` — 메시지는 `snake_case` 동사+대상.
3. **생성 파일 검토** — rename 이 drop+add 로 잡히거나 인덱스·제약 이름이 빠지지 않았는지.
4. 기존 테이블에 필수 컬럼 추가 시 `server_default` 지정.
5. `alembic upgrade head`, 실패 시 `alembic downgrade -1`.
6. 이미 커밋된 마이그레이션은 수정하지 않고 새로 만든다. 컬럼·테이블 삭제는 사용자 확인 후.

---

## 체크리스트

- [ ] `backend/data-model.yaml` 과 완전 일치 + `pytest tests/architecture` 통과?
- [ ] 클래스 단수 / 테이블 복수 snake_case?
- [ ] 메서드(로직·조회) 없음?
- [ ] integer PK + `created_at`/`updated_at`?
- [ ] 모든 FK 에 `ondelete`?
- [ ] unique 제약 이름 `uq_*`?
- [ ] Boolean 컬럼 `is_`/`has_` + `nullable=False` + default?
- [ ] 길이값 상수화, 뻔한 주석 없음?
- [ ] `alembic/env.py` import + 마이그레이션 검토 + `upgrade head` 성공?

## 금지 사항

- ❌ 모델 안 조회·계산·검증 메서드
- ❌ 모델에서 Pydantic·FastAPI·repository import
- ❌ 다른 도메인 모델 클래스 직접 import (문자열 참조)
- ❌ `ondelete` 없는 ForeignKey, 이름 없는 UniqueConstraint
- ❌ 마이그레이션 없이 모델만 변경
- ❌ 약어 컬럼명 (`cnt`, `dt`, `usr_id`)
