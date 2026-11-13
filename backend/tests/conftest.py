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
