"""Unit tests for Policy Service and Policy Source interface interactions."""

from unittest.mock import AsyncMock

import pytest

from app.schemas.policy import (
    PolicyApiDisplaySchemaField,
    PolicyApiSearchResponse,
    PolicyApiSearchResult,
)
from app.services.policy_service import PolicyService


@pytest.mark.asyncio
async def test_policy_service_search_delegates_to_source() -> None:
    """Verifies PolicyService forwards search parameters to PolicySource."""
    mock_source = AsyncMock()
    mock_source.search_policies.return_value = PolicyApiSearchResponse(
        total_results=1,
        display_schema=[
            PolicyApiDisplaySchemaField(id="policy_number", desc="Policy Number", type="string")
        ],
        results=[
            PolicyApiSearchResult(
                display_fields={"policy_number": "POL-123"},
                retrieval_token="token-xyz",
            )
        ],
    )

    service = PolicyService(policy_source=mock_source)
    res = await service.search_policies(
        lob="GL",
        org_external_id="BHSI-ORG-01",
        suborg_external_id="SUB-01",
        search_fields={"policy_number": "POL-123"},
    )

    mock_source.search_policies.assert_awaited_once_with(
        lob="GL",
        org_external_id="BHSI-ORG-01",
        suborg_external_id="SUB-01",
        search_fields={"policy_number": "POL-123"},
    )
    assert res.total_results == 1
    assert res.results[0].retrieval_token == "token-xyz"
