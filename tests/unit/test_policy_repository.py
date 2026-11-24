"""Unit tests for the SQLAlchemy MySQL-backed Policy Repository (Search functionality)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool

from app.core.exceptions import DatabaseError
from app.database.connection import get_engine, init_db
from app.database.models import Base
from app.repositories.policy_repository import MySQLPolicyRepository
from app.schemas.policy import PolicyApiContact, PolicyApiPhone, PolicyApiPolicy


@pytest.fixture
def isolated_repo() -> MySQLPolicyRepository:
    """Provides a fresh isolated MySQLPolicyRepository."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    repo = MySQLPolicyRepository(engine=engine, auto_init=False, auto_seed=False)
    repo.load_mock_data()
    return repo


def test_database_connection_and_engine() -> None:
    """Verifies database engine creation and URL configuration."""
    engine = get_engine("sqlite:///:memory:")
    assert engine is not None
    with engine.connect() as conn:
        assert conn is not None


def test_database_initialization() -> None:
    """Verifies init_db creates all required tables (policies, contacts, phones, tokens)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    assert "policies" in Base.metadata.tables
    assert "policy_contacts" in Base.metadata.tables
    assert "contact_phones" in Base.metadata.tables
    assert "retrieval_tokens" in Base.metadata.tables


def test_repository_save_policy_and_token(isolated_repo: MySQLPolicyRepository) -> None:
    """Verifies inserting a mock policy with nested contacts and phones and creating token."""
    new_policy = PolicyApiPolicy(
        version=1,
        external_id="POL-SQL-999",
        policy_number="BHSI-SQL-999",
        effective_date="2024-01-01",
        expiration_date="2025-01-01",
        policy_holder_contact_ref_id="CNT-SQL",
        lob="GL",
        contacts=[
            PolicyApiContact(
                ref_id="CNT-SQL",
                is_company=True,
                company_name="MySQL Holdings LLC",
                phones=[PolicyApiPhone(phone_number="+1-800-555-9999", phone_type="office")],
            )
        ],
    )
    isolated_repo.save_policy(new_policy, org_external_id="BHSI-ORG-TEST")

    # Generate retrieval token
    token = isolated_repo.create_retrieval_token("POL-SQL-999")
    assert token is not None
    assert len(token) > 20


@pytest.mark.asyncio
async def test_repository_search_single_match(isolated_repo: MySQLPolicyRepository) -> None:
    """Verifies searching with specific criteria returns a single matching policy."""
    response = await isolated_repo.search_policies(
        lob="GL",
        org_external_id="BHSI-ORG-01",
        search_fields={"policy_number": "BHSI-GL-2024-001"},
    )
    assert response.total_results == 1
    assert len(response.results) == 1
    result = response.results[0]
    assert result.display_fields["policy_number"] == "BHSI-GL-2024-001"
    assert result.display_fields["policy_holder"] == "Acme Corporation"
    assert result.retrieval_token is not None


@pytest.mark.asyncio
async def test_repository_search_multiple_matches(isolated_repo: MySQLPolicyRepository) -> None:
    """Verifies searching broad criteria returns multiple matching policies."""
    response = await isolated_repo.search_policies(
        lob="GL",
        org_external_id="BHSI-ORG-01",
    )
    assert response.total_results == 2
    assert len(response.results) == 2


@pytest.mark.asyncio
async def test_repository_search_no_match(isolated_repo: MySQLPolicyRepository) -> None:
    """Verifies searching non-existent criteria returns empty results list with total_results=0."""
    response = await isolated_repo.search_policies(
        lob="NON_EXISTENT_LOB",
        org_external_id="BHSI-ORG-01",
    )
    assert response.total_results == 0
    assert response.results == []
    assert len(response.display_schema) > 0


def test_repository_database_connection_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies database operational or connection failures are wrapped in DatabaseError (500)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    repo = MySQLPolicyRepository(engine=engine, auto_init=False, auto_seed=False)

    def mock_fail(*args: object, **kwargs: object) -> None:
        raise OperationalError(
            statement="SELECT 1",
            params=None,
            orig=Exception("Can't connect to MySQL server on 'localhost' (111)"),
        )

    monkeypatch.setattr(repo.session_factory, "__call__", mock_fail)

    with pytest.raises(DatabaseError) as exc_info:
        repo.save_policy(
            PolicyApiPolicy(
                version=1,
                external_id="POL-FAIL",
                policy_number="FAIL",
                effective_date="2024-01-01",
                expiration_date="2025-01-01",
                policy_holder_contact_ref_id="CNT-1",
                lob="GL",
                contacts=[PolicyApiContact(ref_id="CNT-1")],
            )
        )
    assert exc_info.value.status_code == 500
    assert exc_info.value.code == "DATABASE_ERROR"
