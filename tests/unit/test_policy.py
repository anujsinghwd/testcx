"""Unit tests for Policy Service and Policy Source interface interactions."""

from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import PolicyNotFoundError
from app.schemas.policy import (
    PolicyApiContact,
    PolicyApiDisplaySchemaField,
    PolicyApiPhone,
    PolicyApiPolicy,
    PolicyApiRetrieveResponse,
    PolicyApiSearchResponse,
    PolicyApiSearchResult,
)
from app.services.policy_service import PolicyService


@pytest.mark.asyncio
async def test_policy_service_search_delegates_with_all_params() -> None:
    """Verifies PolicyService forwards all parameters to PolicySource."""
    mock_source = AsyncMock()
    mock_source.search_policies.return_value = PolicyApiSearchResponse(
        total_results=1,
        display_schema=[
            PolicyApiDisplaySchemaField(id="policy_number", desc="Policy Number", type="string"),
            PolicyApiDisplaySchemaField(id="insured_name", desc="Insured", type="string"),
            PolicyApiDisplaySchemaField(id="effective_date", desc="Effective Date", type="date"),
            PolicyApiDisplaySchemaField(id="expiration_date", desc="Expiration Date", type="date"),
        ],
        results=[
            PolicyApiSearchResult(
                display_fields={
                    "policy_number": "BHSI-GL-2024-001",
                    "insured_name": "Acme Corporation",
                    "effective_date": "2024-01-01",
                    "expiration_date": "2025-01-01",
                },
                retrieval_token="token-xyz",
            )
        ],
    )

    service = PolicyService(policy_source=mock_source)
    res = await service.search_policies(
        lob="GL",
        org_external_id="BHSI-ORG-01",
        suborg_external_id="BHSI-SUB-01",
        policy_number="BHSI-GL-2024-001",
    )

    mock_source.search_policies.assert_awaited_once_with(
        lob="GL",
        org_external_id="BHSI-ORG-01",
        suborg_external_id="BHSI-SUB-01",
        policy_number="BHSI-GL-2024-001",
    )
    assert res.total_results == 1
    assert res.results[0].display_fields["insured_name"] == "Acme Corporation"
    assert res.results[0].retrieval_token == "token-xyz"


@pytest.mark.asyncio
async def test_policy_service_search_delegates_without_optional_params() -> None:
    """Verifies PolicyService forwards None for optional parameters when omitted."""
    mock_source = AsyncMock()
    mock_source.search_policies.return_value = PolicyApiSearchResponse(
        total_results=2,
        display_schema=[
            PolicyApiDisplaySchemaField(id="policy_number", desc="Policy Number", type="string"),
            PolicyApiDisplaySchemaField(id="insured_name", desc="Insured", type="string"),
        ],
        results=[],
    )

    service = PolicyService(policy_source=mock_source)
    res = await service.search_policies(
        lob="GL",
        org_external_id="BHSI-ORG-01",
    )

    mock_source.search_policies.assert_awaited_once_with(
        lob="GL",
        org_external_id="BHSI-ORG-01",
        suborg_external_id=None,
        policy_number=None,
    )
    assert res.total_results == 2


@pytest.mark.asyncio
async def test_policy_service_retrieve_by_token_delegates() -> None:
    """Verifies PolicyService forwards retrieval token to PolicySource."""
    mock_source = AsyncMock()
    dummy_policy = PolicyApiPolicy(
        version=1,
        external_id="POL-001",
        policy_number="BHSI-GL-2024-001",
        effective_date="2024-01-01",
        expiration_date="2025-01-01",
        policy_holder_contact_ref_id="CNT-001",
        lob="GL",
        contacts=[
            PolicyApiContact(
                ref_id="CNT-001",
                is_company=True,
                company_name="Acme Corp",
                phones=[PolicyApiPhone(phone_number="555-0100")],
            )
        ],
    )
    mock_source.retrieve_policy_by_token.return_value = PolicyApiRetrieveResponse(
        policy=dummy_policy
    )

    service = PolicyService(policy_source=mock_source)
    res = await service.retrieve_policy_by_token(retrieval_token="token-xyz")

    mock_source.retrieve_policy_by_token.assert_awaited_once_with(retrieval_token="token-xyz")
    assert res.policy.external_id == "POL-001"
    assert res.policy.policy_number == "BHSI-GL-2024-001"
    assert res.policy.contacts[0].company_name == "Acme Corp"


@pytest.mark.asyncio
async def test_policy_service_retrieve_by_token_raises_when_not_found() -> None:
    """Verifies PolicyService propagates PolicyNotFoundError when token does not exist."""
    mock_source = AsyncMock()
    mock_source.retrieve_policy_by_token.side_effect = PolicyNotFoundError("Token not found")

    service = PolicyService(policy_source=mock_source)
    with pytest.raises(PolicyNotFoundError, match="Token not found"):
        await service.retrieve_policy_by_token(retrieval_token="unknown-token")


@pytest.mark.asyncio
async def test_policy_service_retrieve_by_external_id_delegates() -> None:
    """Verifies PolicyService forwards all external ID and claim parameters to PolicySource."""
    mock_source = AsyncMock()
    dummy_policy = PolicyApiPolicy(
        version=1,
        external_id="POL-001",
        policy_number="BHSI-GL-2024-001",
        effective_date="2024-01-01",
        expiration_date="2025-01-01",
        policy_holder_contact_ref_id="CNT-001",
        lob="GL",
        contacts=[
            PolicyApiContact(
                ref_id="CNT-001",
                is_company=True,
                company_name="Acme Corp",
                phones=[PolicyApiPhone(phone_number="555-0100")],
            )
        ],
    )
    mock_source.retrieve_policy_by_external_id.return_value = PolicyApiRetrieveResponse(
        policy=dummy_policy
    )

    service = PolicyService(policy_source=mock_source)
    res = await service.retrieve_policy_by_external_id(
        external_id="POL-001",
        policy_number="BHSI-GL-2024-001",
        date_of_loss="2024-06-15",
        claim_number="CLM-001",
        lob="GL",
        org_external_id="BHSI-ORG-01",
        suborg_external_id="BHSI-SUB-01",
    )

    mock_source.retrieve_policy_by_external_id.assert_awaited_once_with(
        external_id="POL-001",
        policy_number="BHSI-GL-2024-001",
        date_of_loss="2024-06-15",
        claim_number="CLM-001",
        lob="GL",
        org_external_id="BHSI-ORG-01",
        suborg_external_id="BHSI-SUB-01",
    )
    assert res.policy.external_id == "POL-001"
    assert res.policy.policy_number == "BHSI-GL-2024-001"


@pytest.mark.asyncio
async def test_policy_service_retrieve_by_external_id_raises_when_not_found() -> None:
    """Verifies PolicyService propagates PolicyNotFoundError when external_id is not found."""
    mock_source = AsyncMock()
    mock_source.retrieve_policy_by_external_id.side_effect = PolicyNotFoundError("Policy not found")

    service = PolicyService(policy_source=mock_source)
    with pytest.raises(PolicyNotFoundError, match="Policy not found"):
        await service.retrieve_policy_by_external_id(
            external_id="POL-999",
            policy_number="NUM-999",
            date_of_loss="2024-06-15",
            claim_number="CLM-001",
            lob="GL",
            org_external_id="BHSI-ORG-01",
            suborg_external_id="BHSI-SUB-01",
        )
