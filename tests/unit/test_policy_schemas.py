"""Unit tests for Five Sigma v2 Policy API schemas and component contract alignment."""

from typing import Any

import pytest
from pydantic import ValidationError

from app.schemas.policy import (
    DisplayFieldType,
    PolicyApiAddress,
    PolicyApiContact,
    PolicyApiDisplaySchemaField,
    PolicyApiPhone,
    PolicyApiPolicy,
    PolicyApiRetrieveResponse,
    PolicyApiSearchResponse,
    PolicyApiSearchResult,
    PolicySearchRequest,
)

# ==============================================================================
# 1. PolicyApiDisplaySchemaField & DisplayFieldType Enum
# ==============================================================================


def test_display_schema_field_valid_enums() -> None:
    """Verifies string, date, and select enum values are accepted."""
    for valid_type in ["string", "date", "select"]:
        field = PolicyApiDisplaySchemaField(
            id="pol_num",
            desc="Policy Number",
            type=valid_type,  # type: ignore[arg-type]
        )
        assert field.type == valid_type
        assert str(field.type) == valid_type


def test_display_schema_field_invalid_enum_rejected() -> None:
    """Verifies unapproved enum types are rejected with a ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PolicyApiDisplaySchemaField.model_validate(
            {
                "id": "test_id",
                "desc": "Description",
                "type": "unsupported_type",
            }
        )
    assert "Input should be 'string', 'date' or 'select'" in str(exc_info.value)


def test_display_schema_field_required_fields() -> None:
    """Verifies all three fields (id, desc, type) are mandatory."""
    with pytest.raises(ValidationError):
        PolicyApiDisplaySchemaField.model_validate({"desc": "Desc", "type": "string"})

    with pytest.raises(ValidationError):
        PolicyApiDisplaySchemaField.model_validate({"id": "id_1", "type": "string"})

    with pytest.raises(ValidationError):
        PolicyApiDisplaySchemaField.model_validate({"id": "id_1", "desc": "Desc"})


# ==============================================================================
# 2. PolicyApiSearchResult & PolicyApiSearchResponse
# ==============================================================================


def test_search_result_valid() -> None:
    """Verifies PolicyApiSearchResult accepts dynamic string display fields and token."""
    result = PolicyApiSearchResult(
        display_fields={
            "policy_number": "BHSI-GL-2024-001",
            "insured_name": "Acme Corp",
            "effective_date": "2024-01-01",
            "expiration_date": "2025-01-01",
        },
        retrieval_token="token-abc-123",
    )
    assert result.retrieval_token == "token-abc-123"
    assert result.display_fields["policy_number"] == "BHSI-GL-2024-001"


def test_search_result_required_fields() -> None:
    """Verifies display_fields and retrieval_token are both strictly required."""
    with pytest.raises(ValidationError):
        PolicyApiSearchResult.model_validate({"retrieval_token": "token-123"})

    with pytest.raises(ValidationError):
        PolicyApiSearchResult.model_validate({"display_fields": {"policy_number": "123"}})


def test_search_response_valid() -> None:
    """Verifies PolicyApiSearchResponse serializes total_results, display_schema, results."""
    response = PolicyApiSearchResponse(
        total_results=1,
        display_schema=[
            PolicyApiDisplaySchemaField(
                id="policy_number", desc="Policy Number", type=DisplayFieldType.STRING
            )
        ],
        results=[
            PolicyApiSearchResult(
                display_fields={"policy_number": "BHSI-001"},
                retrieval_token="tok-1",
            )
        ],
    )
    assert response.total_results == 1
    assert len(response.display_schema) == 1
    assert len(response.results) == 1


def test_search_response_negative_total_results_rejected() -> None:
    """Verifies total_results minimum value constraint (ge=0) is enforced."""
    empty_schema: list[PolicyApiDisplaySchemaField] = []
    empty_results: list[PolicyApiSearchResult] = []
    invalid_payload: dict[str, Any] = {
        "total_results": int("-1"),
        "display_schema": empty_schema,
        "results": empty_results,
    }
    with pytest.raises(ValidationError) as exc_info:
        PolicyApiSearchResponse.model_validate(invalid_payload)
    assert "Input should be greater than or equal to 0" in str(exc_info.value)


def test_search_response_extra_fields_ignored() -> None:
    """Verifies unapproved extra fields on responses are ignored and not leaked."""
    empty_schema: list[PolicyApiDisplaySchemaField] = []
    empty_results: list[PolicyApiSearchResult] = []
    payload: dict[str, Any] = {
        "total_results": 0,
        "display_schema": empty_schema,
        "results": empty_results,
        "unexpected_extra_field": "should_be_stripped",
    }
    response = PolicyApiSearchResponse.model_validate(payload)
    dumped = response.model_dump()
    assert "unexpected_extra_field" not in dumped


# ==============================================================================
# 3. PolicyApiPhone & PolicyApiAddress
# ==============================================================================


def test_phone_valid() -> None:
    """Verifies phone model accepts phone_number and optional phone_type."""
    phone = PolicyApiPhone(phone_number="617-555-0100", phone_type="office")
    assert phone.phone_number == "617-555-0100"
    assert phone.phone_type == "office"

    phone_no_type = PolicyApiPhone(phone_number="617-555-0199")
    assert phone_no_type.phone_type is None


def test_phone_required_number() -> None:
    """Verifies phone_number is required."""
    with pytest.raises(ValidationError):
        PolicyApiPhone.model_validate({"phone_type": "mobile"})


def test_address_model_fields() -> None:
    """Verifies PolicyApiAddress accepts standard address properties."""
    address = PolicyApiAddress(
        address1="100 Example St",
        address2="Suite 200",
        city="Boston",
        state="MA",
        zipcode="02110",
        country="US",
    )
    assert address.address1 == "100 Example St"
    assert address.city == "Boston"
    assert address.state == "MA"


# ==============================================================================
# 4. PolicyApiContact
# ==============================================================================


def test_contact_company_valid() -> None:
    """Verifies corporate contact record creation."""
    contact = PolicyApiContact(
        ref_id="CNT-001",
        external_id="PAS-CNT-000456",
        is_company=True,
        company_name="Krazy Kuts Barber Shop",
        phones=[PolicyApiPhone(phone_number="617-555-0100", phone_type="office")],
        address1="100 Example Street",
        city="Boston",
        state="MA",
        zipcode="02110",
        country="US",
    )
    assert contact.ref_id == "CNT-001"
    assert contact.is_company is True
    assert contact.company_name == "Krazy Kuts Barber Shop"
    assert contact.first_name is None
    assert len(contact.phones) == 1


def test_contact_individual_valid() -> None:
    """Verifies individual person contact record creation."""
    contact = PolicyApiContact(
        ref_id="CNT-002",
        is_company=False,
        first_name="Jane",
        middle_name="M.",
        last_name="Smith",
        phones=[PolicyApiPhone(phone_number="+1-617-555-0199", phone_type="mobile")],
    )
    assert contact.ref_id == "CNT-002"
    assert contact.is_company is False
    assert contact.first_name == "Jane"
    assert contact.last_name == "Smith"


def test_contact_required_ref_id() -> None:
    """Verifies ref_id is mandatory on contacts."""
    with pytest.raises(ValidationError):
        PolicyApiContact.model_validate({"is_company": True, "company_name": "Acme"})


# ==============================================================================
# 5. PolicyApiPolicy & PolicyApiRetrieveResponse
# ==============================================================================


def test_policy_schema_full_contract_example() -> None:
    """Verifies the complete PolicyApiPolicy matching the Five Sigma v2 contract example."""
    policy_data = {
        "version": 1,
        "external_id": "PAS-POL-000123",
        "policy_number": "BHSI-GL-26-000123",
        "effective_date": "2025-10-20",
        "expiration_date": "2026-10-20",
        "effective_time": "00:00",
        "expiration_time": "00:00",
        "policy_holder_contact_ref_id": "1",
        "lob": "general_policy",
        "sub_organization_external_id": "bhsi_suborg_id",
        "is_claims_made": False,
        "contacts": [
            {
                "ref_id": "1",
                "external_id": "PAS-CNT-000456",
                "is_company": True,
                "company_name": "Krazy Kuts Barber Shop",
                "phones": [{"phone_number": "617-555-0100", "phone_type": "office"}],
                "address1": "100 Example Street",
                "city": "Boston",
                "state": "MA",
                "zipcode": "02110",
                "country": "US",
            }
        ],
    }
    policy = PolicyApiPolicy.model_validate(policy_data)
    assert policy.version == 1
    assert policy.policy_number == "BHSI-GL-26-000123"
    assert policy.lob == "general_policy"
    assert policy.contacts[0].company_name == "Krazy Kuts Barber Shop"

    # Wrap in retrieval response
    retrieve_response = PolicyApiRetrieveResponse(policy=policy)
    dumped = retrieve_response.model_dump(exclude_none=True)
    assert "policy" in dumped
    assert dumped["policy"]["external_id"] == "PAS-POL-000123"
    assert dumped["policy"]["contacts"][0]["phones"][0]["phone_number"] == "617-555-0100"


def test_policy_schema_required_fields_enforcement() -> None:
    """Verifies that missing any of the 8 mandatory policy fields fails validation."""
    base_data = {
        "version": 1,
        "external_id": "POL-1",
        "policy_number": "NUM-1",
        "effective_date": "2024-01-01",
        "expiration_date": "2025-01-01",
        "policy_holder_contact_ref_id": "CNT-1",
        "lob": "GL",
        "contacts": [{"ref_id": "CNT-1"}],
    }

    # Verify baseline is valid
    assert PolicyApiPolicy.model_validate(base_data).external_id == "POL-1"

    # Test omitting each required field
    required_fields = [
        "external_id",
        "policy_number",
        "effective_date",
        "expiration_date",
        "policy_holder_contact_ref_id",
        "lob",
        "contacts",
    ]
    for field_name in required_fields:
        invalid_data = {k: v for k, v in base_data.items() if k != field_name}
        with pytest.raises(ValidationError):
            PolicyApiPolicy.model_validate(invalid_data)


def test_policy_schema_empty_contacts_rejected() -> None:
    """Verifies contacts list must contain at least 1 contact (min_length=1)."""
    empty_contacts: list[PolicyApiContact] = []
    payload: dict[str, Any] = {
        "version": 1,
        "external_id": "POL-1",
        "policy_number": "NUM-1",
        "effective_date": "2024-01-01",
        "expiration_date": "2025-01-01",
        "policy_holder_contact_ref_id": "CNT-1",
        "lob": "GL",
        "contacts": empty_contacts,
    }
    with pytest.raises(ValidationError) as exc_info:
        PolicyApiPolicy.model_validate(payload)
    assert "List should have at least 1 item" in str(exc_info.value)


def test_policy_schema_unexpected_fields_ignored() -> None:
    """Verifies unexpected extra fields in policy records are ignored and not leaked."""
    payload = {
        "version": 1,
        "external_id": "POL-1",
        "policy_number": "NUM-1",
        "effective_date": "2024-01-01",
        "expiration_date": "2025-01-01",
        "policy_holder_contact_ref_id": "CNT-1",
        "lob": "GL",
        "contacts": [{"ref_id": "CNT-1"}],
        "non_contract_internal_db_column": "should_be_ignored",
    }
    policy = PolicyApiPolicy.model_validate(payload)
    dumped = policy.model_dump()
    assert "non_contract_internal_db_column" not in dumped


# ==============================================================================
# 6. PolicySearchRequest
# ==============================================================================


def test_search_request_valid() -> None:
    """Verifies PolicySearchRequest validates required lob and org_external_id."""
    req = PolicySearchRequest(lob="GL", org_external_id="BHSI-ORG-01")
    assert req.lob == "GL"
    assert req.org_external_id == "BHSI-ORG-01"
    assert req.suborg_external_id is None
    assert req.policy_number is None


def test_search_request_additional_properties_allowed() -> None:
    """Verifies PolicySearchRequest supports extra configured search parameters."""
    req = PolicySearchRequest.model_validate(
        {
            "lob": "GL",
            "org_external_id": "BHSI-ORG-01",
            "custom_search_field": "custom_value",
        }
    )
    assert req.lob == "GL"
    assert getattr(req, "custom_search_field", None) == "custom_value" or (
        req.model_extra is not None and req.model_extra.get("custom_search_field") == "custom_value"
    )
