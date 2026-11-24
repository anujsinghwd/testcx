"""Unit tests for the SQLAlchemy MySQL-backed Policy Repository (Search functionality)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool

from app.core.exceptions import DatabaseError, PolicyNotFoundError
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
async def test_repository_search_with_required_lob_and_org(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies searching using required lob and org_external_id returns matching policies."""
    response = await isolated_repo.search_policies(
        lob="GL",
        org_external_id="BHSI-ORG-01",
    )
    assert response.total_results == 2
    assert len(response.results) == 2


@pytest.mark.asyncio
async def test_repository_search_with_optional_suborg_external_id(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies searching with optional suborg_external_id filters to the specific suborg."""
    response = await isolated_repo.search_policies(
        lob="GL",
        org_external_id="BHSI-ORG-01",
        suborg_external_id="BHSI-SUB-01",
    )
    assert response.total_results == 1
    assert len(response.results) == 1
    assert response.results[0].display_fields["policy_number"] == "BHSI-GL-2024-001"


@pytest.mark.asyncio
async def test_repository_search_with_optional_policy_number(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies searching with optional policy_number returns a single matching policy."""
    response = await isolated_repo.search_policies(
        lob="GL",
        org_external_id="BHSI-ORG-01",
        policy_number="BHSI-GL-2024-001",
    )
    assert response.total_results == 1
    assert len(response.results) == 1
    result = response.results[0]
    assert result.display_fields["policy_number"] == "BHSI-GL-2024-001"
    assert result.display_fields["insured_name"] == "Acme Corporation"
    assert result.display_fields["effective_date"] == "2024-01-01"
    assert result.display_fields["expiration_date"] == "2025-01-01"
    assert result.retrieval_token is not None


@pytest.mark.asyncio
async def test_repository_search_without_policy_number(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies searching without policy_number returns all policies matching LOB and org."""
    response = await isolated_repo.search_policies(
        lob="GL",
        org_external_id="BHSI-ORG-01",
        policy_number=None,
    )
    assert response.total_results == 2
    assert len(response.results) == 2


@pytest.mark.asyncio
async def test_repository_search_display_schema_matches_v2_contract(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies display_schema has exact 4 fields from Five Sigma v2 contract."""
    response = await isolated_repo.search_policies(
        lob="GL",
        org_external_id="BHSI-ORG-01",
    )
    schema_ids = [field.id for field in response.display_schema]
    assert schema_ids == ["policy_number", "insured_name", "effective_date", "expiration_date"]

    # Verify field descriptions and types
    fields_by_id = {f.id: f for f in response.display_schema}
    assert fields_by_id["policy_number"].desc == "Policy Number"
    assert fields_by_id["policy_number"].type == "string"
    assert fields_by_id["insured_name"].desc == "Insured"
    assert fields_by_id["insured_name"].type == "string"
    assert fields_by_id["effective_date"].desc == "Effective Date"
    assert fields_by_id["effective_date"].type == "date"
    assert fields_by_id["expiration_date"].desc == "Expiration Date"
    assert fields_by_id["expiration_date"].type == "date"


@pytest.mark.asyncio
async def test_repository_search_no_matching_records(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies searching non-existent criteria returns empty results list with total_results=0."""
    response = await isolated_repo.search_policies(
        lob="NON_EXISTENT_LOB",
        org_external_id="BHSI-ORG-01",
    )
    assert response.total_results == 0
    assert response.results == []
    assert len(response.display_schema) == 4


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


@pytest.mark.asyncio
async def test_repository_retrieve_by_token_success(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies retrieving a policy using a valid token returns full policy with contacts & phones."""
    token = isolated_repo.create_retrieval_token("POL-BHSI-001")
    response = await isolated_repo.retrieve_policy_by_token(token)

    assert response.policy.external_id == "POL-BHSI-001"
    assert response.policy.policy_number == "BHSI-GL-2024-001"
    assert response.policy.lob == "GL"
    assert len(response.policy.contacts) == 1
    contact = response.policy.contacts[0]
    assert contact.ref_id == "CNT-001"
    assert contact.is_company is True
    assert contact.company_name == "Acme Corporation"
    assert len(contact.phones) == 1
    assert contact.phones[0].phone_number == "+1-800-555-0100"


@pytest.mark.asyncio
async def test_repository_retrieve_by_token_not_found(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies retrieving with an unknown token raises PolicyNotFoundError (404)."""
    with pytest.raises(PolicyNotFoundError) as exc_info:
        await isolated_repo.retrieve_policy_by_token("non-existent-token-abc")
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "NOT_FOUND"


@pytest.mark.asyncio
async def test_repository_retrieve_by_token_isolation(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies each token strictly retrieves only its associated policy and not another."""
    token_1 = isolated_repo.create_retrieval_token("POL-BHSI-001")
    token_2 = isolated_repo.create_retrieval_token("POL-BHSI-002")

    res_1 = await isolated_repo.retrieve_policy_by_token(token_1)
    res_2 = await isolated_repo.retrieve_policy_by_token(token_2)

    assert res_1.policy.external_id == "POL-BHSI-001"
    assert res_1.policy.policy_number == "BHSI-GL-2024-001"

    assert res_2.policy.external_id == "POL-BHSI-002"
    assert res_2.policy.policy_number == "BHSI-PROP-2024-002"


@pytest.mark.asyncio
async def test_repository_retrieve_by_token_consistency(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies repeated retrievals using the exact same token yield identical results."""
    token = isolated_repo.create_retrieval_token("POL-BHSI-001")

    res_first = await isolated_repo.retrieve_policy_by_token(token)
    res_second = await isolated_repo.retrieve_policy_by_token(token)

    assert res_first.model_dump() == res_second.model_dump()


@pytest.mark.asyncio
async def test_repository_retrieve_by_token_database_failure(
    isolated_repo: MySQLPolicyRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies database failures during retrieval raise DatabaseError (500)."""

    def mock_session_factory() -> None:
        raise OperationalError(
            statement="SELECT * FROM retrieval_tokens",
            params=None,
            orig=Exception("Connection lost"),
        )

    monkeypatch.setattr(isolated_repo, "session_factory", mock_session_factory)

    with pytest.raises(DatabaseError) as exc_info:
        await isolated_repo.retrieve_policy_by_token("some-token")
    assert exc_info.value.status_code == 500
    assert exc_info.value.code == "DATABASE_ERROR"


@pytest.mark.asyncio
async def test_repository_retrieve_by_external_id_success(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies retrieving by external ID when in force on date of loss returns complete policy."""
    response = await isolated_repo.retrieve_policy_by_external_id(
        external_id="POL-BHSI-001",
        policy_number="BHSI-GL-2024-001",
        date_of_loss="2024-06-15",
        claim_number="CLM-001",
        lob="GL",
        org_external_id="BHSI-ORG-01",
        suborg_external_id="BHSI-SUB-01",
    )
    assert response.policy.external_id == "POL-BHSI-001"
    assert response.policy.policy_number == "BHSI-GL-2024-001"
    assert response.policy.effective_date == "2024-01-01"
    assert response.policy.expiration_date == "2025-01-01"
    assert len(response.policy.contacts) == 1


@pytest.mark.asyncio
async def test_repository_retrieve_by_external_id_not_in_force_before_effective(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies date of loss prior to policy effective date raises PolicyNotFoundError (404)."""
    with pytest.raises(PolicyNotFoundError, match="was not in force on date of loss"):
        await isolated_repo.retrieve_policy_by_external_id(
            external_id="POL-BHSI-001",
            policy_number="BHSI-GL-2024-001",
            date_of_loss="2023-12-31",
            claim_number="CLM-001",
            lob="GL",
            org_external_id="BHSI-ORG-01",
            suborg_external_id="BHSI-SUB-01",
        )


@pytest.mark.asyncio
async def test_repository_retrieve_by_external_id_not_in_force_after_expiration(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies date of loss after policy expiration date raises PolicyNotFoundError (404)."""
    with pytest.raises(PolicyNotFoundError, match="was not in force on date of loss"):
        await isolated_repo.retrieve_policy_by_external_id(
            external_id="POL-BHSI-001",
            policy_number="BHSI-GL-2024-001",
            date_of_loss="2025-01-02",
            claim_number="CLM-001",
            lob="GL",
            org_external_id="BHSI-ORG-01",
            suborg_external_id="BHSI-SUB-01",
        )


@pytest.mark.asyncio
async def test_repository_retrieve_by_external_id_not_in_force_after_cancellation(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies date of loss after cancellation date raises PolicyNotFoundError (404)."""
    cancelled_policy = PolicyApiPolicy(
        version=1,
        external_id="POL-CANCELLED",
        policy_number="BHSI-CNL-001",
        effective_date="2024-01-01",
        expiration_date="2025-01-01",
        cancelled_date="2024-05-01",
        policy_holder_contact_ref_id="CNT-001",
        lob="GL",
        sub_organization_external_id="BHSI-SUB-01",
        contacts=[
            PolicyApiContact(
                ref_id="CNT-001",
                is_company=True,
                company_name="Cancelled Inc",
            )
        ],
    )
    isolated_repo.save_policy(cancelled_policy, org_external_id="BHSI-ORG-01")

    # Date of loss after cancellation
    with pytest.raises(PolicyNotFoundError, match="was not in force on date of loss"):
        await isolated_repo.retrieve_policy_by_external_id(
            external_id="POL-CANCELLED",
            policy_number="BHSI-CNL-001",
            date_of_loss="2024-05-15",
            claim_number="CLM-001",
            lob="GL",
            org_external_id="BHSI-ORG-01",
            suborg_external_id="BHSI-SUB-01",
        )


@pytest.mark.asyncio
async def test_repository_retrieve_by_external_id_claims_made_retroactive(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies claims-made policy with date of loss prior to retroactive date raises 404."""
    with pytest.raises(PolicyNotFoundError, match="was not in force on date of loss"):
        await isolated_repo.retrieve_policy_by_external_id(
            external_id="POL-BHSI-004",
            policy_number="BHSI-XS-2024-004",
            date_of_loss="2023-08-01",  # Retroactive date is 2023-09-01
            claim_number="CLM-001",
            lob="EXCESS",
            org_external_id="BHSI-ORG-02",
            suborg_external_id="BHSI-SUB-02",
        )


@pytest.mark.asyncio
async def test_repository_retrieve_by_external_id_unknown_external_id(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies unknown external_id raises PolicyNotFoundError (404)."""
    with pytest.raises(PolicyNotFoundError, match="not found"):
        await isolated_repo.retrieve_policy_by_external_id(
            external_id="POL-UNKNOWN-999",
            policy_number="BHSI-GL-2024-001",
            date_of_loss="2024-06-15",
            claim_number="CLM-001",
            lob="GL",
            org_external_id="BHSI-ORG-01",
            suborg_external_id="BHSI-SUB-01",
        )


@pytest.mark.asyncio
async def test_repository_retrieve_by_external_id_mismatched_identifiers(
    isolated_repo: MySQLPolicyRepository,
) -> None:
    """Verifies mismatch on policy_number, lob, org, or suborg raises PolicyNotFoundError (404)."""
    # Mismatched policy number
    with pytest.raises(PolicyNotFoundError, match="Policy number"):
        await isolated_repo.retrieve_policy_by_external_id(
            external_id="POL-BHSI-001",
            policy_number="WRONG-NUM",
            date_of_loss="2024-06-15",
            claim_number="CLM-001",
            lob="GL",
            org_external_id="BHSI-ORG-01",
            suborg_external_id="BHSI-SUB-01",
        )

    # Mismatched LOB
    with pytest.raises(PolicyNotFoundError, match="Line of business"):
        await isolated_repo.retrieve_policy_by_external_id(
            external_id="POL-BHSI-001",
            policy_number="BHSI-GL-2024-001",
            date_of_loss="2024-06-15",
            claim_number="CLM-001",
            lob="PROPERTY",
            org_external_id="BHSI-ORG-01",
            suborg_external_id="BHSI-SUB-01",
        )

    # Mismatched Organization
    with pytest.raises(PolicyNotFoundError, match="Organization"):
        await isolated_repo.retrieve_policy_by_external_id(
            external_id="POL-BHSI-001",
            policy_number="BHSI-GL-2024-001",
            date_of_loss="2024-06-15",
            claim_number="CLM-001",
            lob="GL",
            org_external_id="WRONG-ORG",
            suborg_external_id="BHSI-SUB-01",
        )

    # Mismatched Sub-organization
    with pytest.raises(PolicyNotFoundError, match="Sub-organization"):
        await isolated_repo.retrieve_policy_by_external_id(
            external_id="POL-BHSI-001",
            policy_number="BHSI-GL-2024-001",
            date_of_loss="2024-06-15",
            claim_number="CLM-001",
            lob="GL",
            org_external_id="BHSI-ORG-01",
            suborg_external_id="WRONG-SUBORG",
        )


@pytest.mark.asyncio
async def test_repository_retrieve_by_external_id_database_failure(
    isolated_repo: MySQLPolicyRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifies database failures during retrieve_by_external_id raise DatabaseError (500)."""

    def mock_session_factory() -> None:
        raise OperationalError(
            statement="SELECT * FROM policies",
            params=None,
            orig=Exception("Connection lost"),
        )

    monkeypatch.setattr(isolated_repo, "session_factory", mock_session_factory)

    with pytest.raises(DatabaseError) as exc_info:
        await isolated_repo.retrieve_policy_by_external_id(
            external_id="POL-BHSI-001",
            policy_number="BHSI-GL-2024-001",
            date_of_loss="2024-06-15",
            claim_number="CLM-001",
            lob="GL",
            org_external_id="BHSI-ORG-01",
            suborg_external_id="BHSI-SUB-01",
        )
    assert exc_info.value.status_code == 500
    assert exc_info.value.code == "DATABASE_ERROR"
