---
description: backend/tests/ — 백엔드 테스트 작성 또는 수정 시
paths:
  - "backend/tests/**/*.py"
---

# Test Convention — 백엔드 테스트 규칙

공통 코딩 규칙(네이밍·포맷팅·import·주석)은 `python-convention.md` — 기준은 `docs/backend/CONVENTIONS.md`. 테스트 코드도 동일하게 적용한다.

---

## 디렉터리 구조 (강제)

```
tests/
├── conftest.py                          # 공용 픽스처 (db_session, client)
├── architecture/                        # 경계 테스트 (수정 금지)
├── unit/
│   ├── common/
│   │   └── test_handlers.py             # envelope·핸들러
│   ├── scripts/
│   │   └── test_{script}.py               # backend/scripts/ 도구의 판정 로직 (네트워크 없음)
│   └── domains/{domain}/
│       ├── test_repository.py           # 쿼리 (테스트 DB)
│       └── test_service.py              # 유스케이스 (mock repository)
└── api/
    └── test_{domain}.py                 # 엔드포인트 계약 (mock service)
```

## 네이밍

- 파일: `test_{대상 파일명}.py` — 테스트 파일 1개 = 대상 파일 1개.
- 함수: `test_{대상}_{조건}_{기대결과}` — `test_get_post_when_missing_raises_not_found`, `test_create_post_returns_created_envelope`.
- docstring: 한국어 한 줄 — 무엇을 보장하는지.
- 지역 변수 약어 금지 — `repository`, `service`, `response`, `body` (`repo`, `svc`, `res`, `r` ❌).
- 테스트 상수(ID 등)는 모듈 상단 `UPPER_SNAKE_CASE` — `POST_ID = 1`, `MISSING_POST_ID = 9999`.
- 테스트 데이터 팩토리: `make_{entity}(...)` — 모듈 상단(또는 conftest)에 1번만 정의하고 재사용.

## 레이어별 테스트 대상 / 비대상

| 레이어 | 테스트하는 것 | 테스트하지 않는 것 |
|---|---|---|
| repository | 쿼리 조건·정렬·eager load, 없으면 None | 비즈니스 분기, HTTP |
| service | 유스케이스 분기, 도메인 예외, commit 호출 | 실제 SQL (repository mock) |
| router (api) | status code, envelope, 파라미터 바인딩 | 비즈니스 로직 (service mock) |
| common | envelope 변환 4종 | — |

## 핵심 원칙

1. **service 테스트는 `Mock(spec=...)` 주입** — `spec` 필수.
2. **api 테스트는 `app.dependency_overrides` 로 service 교체** — `client` 픽스처가 teardown 에서 `clear()`.
3. **repository 테스트만 DB 사용** — `db_session` 픽스처(테스트별 rollback).
4. **Arrange / Act / Assert 사이 빈 줄 1줄** — 구역 주석(`# given` 등)은 달지 않는다.
5. **Boolean 단언은 `is`** — `assert body["data"]["is_published"] is True`, `assert result is None`. `== True` 금지.
6. **반복 준비 코드는 픽스처·팩토리로** — 같은 mock 세팅이 3번 이상이면 픽스처로 뺀다.
7. **테스트 약화 금지** — `skip`/`xfail` 임의 사용, assertion 삭제, 기대값을 실제값에 맞추기 금지.
8. 실행: `cd backend && .venv/bin/pytest tests/unit/domains/{domain}` 로 좁혀 반복 → Task 완료 시 `make check-backend`.

## conftest 픽스처 규약

```python
# tests/conftest.py
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.base import engine
from app.main import app


@pytest.fixture
def db_session() -> Iterator[Session]:
    """테스트별 트랜잭션 rollback으로 격리된 세션"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client() -> Iterator[TestClient]:
    """dependency_overrides 정리를 보장하는 TestClient"""
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

## service 테스트 템플릿

```python
# tests/unit/domains/post/test_service.py
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.domains.post.exceptions import PostNotFoundException
from app.domains.post.repository import PostRepository
from app.domains.post.service import PostService

MISSING_POST_ID = 9999


@pytest.fixture
def repository() -> Mock:
    """spec 이 걸린 PostRepository mock"""
    return Mock(spec=PostRepository)


@pytest.fixture
def service(repository: Mock) -> PostService:
    """mock 을 주입한 PostService"""
    return PostService(db=Mock(spec=Session), repository=repository)


def test_get_post_when_missing_raises_not_found(service: PostService, repository: Mock) -> None:
    """존재하지 않는 포스트 조회 시 PostNotFoundException"""
    repository.find_by_id.return_value = None

    with pytest.raises(PostNotFoundException):
        service.get_post(MISSING_POST_ID)
```

## api 테스트 템플릿

```python
# tests/api/test_post.py
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.domains.post.exceptions import PostNotFoundException
from app.domains.post.router import get_post_service
from app.domains.post.service import PostService
from app.main import app

POST_ID = 1


def test_get_post_returns_success_envelope(client: TestClient) -> None:
    """단건 조회 성공 시 success envelope을 반환한다"""
    service = Mock(spec=PostService)
    service.get_post.return_value = make_post(id=POST_ID)
    app.dependency_overrides[get_post_service] = lambda: service

    response = client.get(f"/api/posts/{POST_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["id"] == POST_ID
    service.get_post.assert_called_once_with(POST_ID)


def test_get_post_when_missing_returns_fail_envelope(client: TestClient) -> None:
    """없는 포스트 조회 시 404 fail envelope을 반환한다"""
    service = Mock(spec=PostService)
    service.get_post.side_effect = PostNotFoundException()
    app.dependency_overrides[get_post_service] = lambda: service

    response = client.get(f"/api/posts/{POST_ID}")

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "fail"
    assert body["data"]["code"] == 404
```

> `make_post()` 는 응답 스키마 필드를 모두 채운 엔티티(또는 `SimpleNamespace`)를 만드는 팩토리 — 같은 파일 상단이나 conftest 에 한 번만 정의한다.

---

## 체크리스트

- [ ] 디렉터리 구조 + 파일 1:1 대응?
- [ ] 함수명 `test_{대상}_{조건}_{기대결과}` + 한국어 docstring?
- [ ] 변수명 약어 없음 (`repository`, `response`, `test_client`)?
- [ ] service 테스트에 실제 DB 없음 + `Mock(spec=...)`?
- [ ] api 테스트에 비즈니스 검증 없음?
- [ ] Boolean·None 단언이 `is`?
- [ ] 반복 준비 코드가 픽스처·팩토리로?
- [ ] skip/xfail/assertion 약화 없음?
- [ ] `pytest` 전체 통과?

## 금지 사항

- ❌ `spec` 없는 `Mock()` 으로 repository/service 대체
- ❌ service·api 테스트에서 실제 DB 접근
- ❌ `assert x == True` / `assert x == None`
- ❌ 함수 안 import, 약어 변수명 (`repo`, `res`, `c`)
- ❌ 테스트 약화 (`skip`, `xfail`, assertion 삭제, 기대값 조작)
- ❌ `tests/architecture/` 수정·우회
