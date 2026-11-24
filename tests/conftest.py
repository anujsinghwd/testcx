"""Shared pytest configuration, database fixtures, and test client setup."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool

from app.database.models import Base
from app.dependencies.clients import (
    get_mock_policy_repository,
    get_mysql_policy_repository,
    get_policy_source,
)
from app.main import app
from app.repositories.policy_repository import MySQLPolicyRepository


@pytest.fixture(scope="session")
def test_engine() -> Engine:
    """Provides an isolated in-memory SQLite engine using SQLAlchemy for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_repo(test_engine: Engine) -> MySQLPolicyRepository:
    """Provides a cleanly seeded MySQLPolicyRepository instance for each test."""
    repo = MySQLPolicyRepository(
        engine=test_engine,
        auto_init=True,
        auto_seed=False,
    )
    repo.load_mock_data()
    return repo


@pytest.fixture
def client(test_repo: MySQLPolicyRepository) -> Generator[TestClient, None, None]:
    """FastAPI TestClient fixture with isolated test database overrides."""
    app.dependency_overrides[get_mysql_policy_repository] = lambda: test_repo
    app.dependency_overrides[get_mock_policy_repository] = lambda: test_repo
    app.dependency_overrides[get_policy_source] = lambda: test_repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
