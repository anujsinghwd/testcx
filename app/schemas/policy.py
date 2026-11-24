"""Policy schemas adhering to the Five Sigma v2 OpenAPI contract specifications.

All models correspond strictly to the components defined in BHSI_PolicyAPI_v2_contract.json:
- PolicyApiDisplaySchemaField (DisplayFieldType enum: string, date, select)
- PolicyApiSearchResult (display_fields dynamic string mapping, retrieval_token)
- PolicyApiSearchResponse (total_results >= 0, display_schema, results)
- PolicyApiPhone (phone_number, optional phone_type)
- PolicyApiAddress (address1, address2, city, state, zipcode, country)
- PolicyApiContact (ref_id, is_company, company_name, names, phones, addresses)
- PolicyApiPolicy (all canonical policy fields, version, dates, times, contacts, lob)
- PolicyApiRetrieveResponse (top-level policy object)
- PolicySearchRequest (lob, org_external_id, optional suborg_external_id & policy_number)
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DisplayFieldType(StrEnum):
    """Allowed data types for search result display schema fields."""

    STRING = "string"
    DATE = "date"
    SELECT = "select"


class PolicyApiPhone(BaseModel):
    """Phone number record for a policy contact."""

    model_config = ConfigDict(extra="ignore")

    phone_number: str = Field(..., description="Phone number string")
    phone_type: str | None = Field(
        default=None, description="Optional phone type descriptor (e.g. office, mobile, work)"
    )


class PolicyApiAddress(BaseModel):
    """Address details component."""

    model_config = ConfigDict(extra="ignore")

    address1: str | None = Field(default=None, description="Primary street address line")
    address2: str | None = Field(default=None, description="Secondary address line (suite, apt)")
    city: str | None = Field(default=None, description="City name")
    state: str | None = Field(default=None, description="State, province, or region")
    zipcode: str | None = Field(default=None, description="Postal code or ZIP code")
    country: str | None = Field(default=None, description="Country name or ISO code")


class PolicyApiContact(BaseModel):
    """Contact record for a policy (individual or company)."""

    model_config = ConfigDict(extra="ignore")

    ref_id: str = Field(..., description="Unique reference ID of the contact within the policy")
    external_id: str | None = Field(default=None, description="External contact reference ID")
    is_company: bool = Field(
        default=False, description="Flag indicating if contact is a corporate entity"
    )
    company_name: str | None = Field(default=None, description="Company name if is_company is True")
    first_name: str | None = Field(default=None, description="First name if individual contact")
    middle_name: str | None = Field(default=None, description="Middle name if individual contact")
    last_name: str | None = Field(default=None, description="Last name if individual contact")
    phones: list[PolicyApiPhone] = Field(
        default_factory=list, description="Contact phone numbers list"
    )
    address1: str | None = Field(default=None, description="Primary address line")
    address2: str | None = Field(default=None, description="Secondary address line")
    city: str | None = Field(default=None, description="City name")
    state: str | None = Field(default=None, description="State / Province")
    zipcode: str | None = Field(default=None, description="Postal / ZIP code")
    country: str | None = Field(default=None, description="Country code or name")


class PolicyApiPolicy(BaseModel):
    """Full policy model stored in the repository and returned in retrieval responses."""

    model_config = ConfigDict(extra="ignore")

    version: int = Field(default=1, description="Policy version number")
    external_id: str = Field(..., description="External unique identifier for the policy")
    policy_number: str = Field(..., description="Organization policy number")
    effective_date: str = Field(..., description="Policy effective date (YYYY-MM-DD)")
    expiration_date: str = Field(..., description="Policy expiration date (YYYY-MM-DD)")
    policy_holder_contact_ref_id: str = Field(
        ..., description="Reference ID of the contact acting as the primary policyholder"
    )
    contacts: list[PolicyApiContact] = Field(
        ..., min_length=1, description="Contacts associated with the policy"
    )
    lob: str = Field(..., description="Line of business")

    # Optional fields
    retroactive_date: str | None = Field(
        default=None, description="Claims-made retroactive date (YYYY-MM-DD)"
    )
    cancelled_date: str | None = Field(
        default=None, description="Policy cancellation date if cancelled (YYYY-MM-DD)"
    )
    effective_time: str | None = Field(
        default=None, description="Time of day policy becomes effective (HH:MM)"
    )
    expiration_time: str | None = Field(
        default=None, description="Time of day policy expires (HH:MM)"
    )
    cancelled_time: str | None = Field(
        default=None, description="Time of day policy was cancelled (HH:MM)"
    )
    retroactive_time: str | None = Field(
        default=None, description="Time of day retroactive boundary takes effect"
    )
    sub_organization_external_id: str | None = Field(
        default=None, description="Sub-organization external ID"
    )
    is_claims_made: bool | None = Field(
        default=None, description="Flag indicating claims-made coverage"
    )
    runoff_provision: str | None = Field(
        default=None, description="Runoff provision terms if applicable"
    )


class PolicyApiDisplaySchemaField(BaseModel):
    """Schema descriptor for a search result display column."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique field identifier matching display_fields key")
    desc: str = Field(..., description="Human-readable column label for UI display")
    type: DisplayFieldType | Literal["string", "date", "select"] = Field(
        ..., description="Data type: string, date, or select"
    )


class PolicyApiSearchResult(BaseModel):
    """Individual search result item containing display values and retrieval token."""

    model_config = ConfigDict(extra="ignore")

    display_fields: dict[str, str] = Field(
        ..., description="Dynamic string values keyed by the corresponding display_schema.id"
    )
    retrieval_token: str = Field(..., description="Opaque token for policy retrieval")


class PolicyApiSearchResponse(BaseModel):
    """Response model for the GET and POST /policies/search endpoints."""

    model_config = ConfigDict(extra="ignore")

    total_results: int = Field(..., ge=0, description="Total number of matching results (min: 0)")
    display_schema: list[PolicyApiDisplaySchemaField] = Field(
        ..., description="Ordered list of display column descriptors"
    )
    results: list[PolicyApiSearchResult] = Field(..., description="Matching search result items")


class PolicySearchRequest(BaseModel):
    """Request model for POST /policies/search endpoint adhering to Five Sigma v2 contract."""

    model_config = ConfigDict(extra="allow")

    lob: str = Field(..., description="Line of business. Exactly one value.")
    org_external_id: str = Field(..., description="External ID of the Five Sigma organization.")
    suborg_external_id: str | None = Field(
        default=None, description="Sub-organization external ID."
    )
    policy_number: str | None = Field(
        default=None, description="Optional organization-configured search field."
    )


class PolicyApiRetrieveResponse(BaseModel):
    """Response model for policy retrieval endpoints adhering to Five Sigma v2 contract."""

    model_config = ConfigDict(extra="ignore")

    policy: PolicyApiPolicy = Field(..., description="Complete policy object")
