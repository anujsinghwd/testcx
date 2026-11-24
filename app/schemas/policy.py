"""Policy schemas adhering to the Five Sigma v2 Policy Search contract."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PolicyApiPhone(BaseModel):
    """Phone number record for a policy contact."""

    model_config = ConfigDict(extra="allow")

    phone_number: str
    phone_type: str | None = None


class PolicyApiContact(BaseModel):
    """Contact record for a policy (individual or company)."""

    model_config = ConfigDict(extra="allow")

    ref_id: str
    external_id: str | None = None
    is_company: bool = False
    company_name: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    phones: list[PolicyApiPhone] = Field(default_factory=list)
    address1: str | None = None
    address2: str | None = None
    city: str | None = None
    state: str | None = None
    zipcode: str | None = None
    country: str | None = None


class PolicyApiPolicy(BaseModel):
    """Full policy model stored in the repository and used to build search display fields."""

    model_config = ConfigDict(extra="allow")

    version: int = 1
    external_id: str
    policy_number: str
    effective_date: str
    expiration_date: str
    policy_holder_contact_ref_id: str
    contacts: list[PolicyApiContact] = Field(min_length=1)
    lob: str

    # Optional fields
    retroactive_date: str | None = None
    cancelled_date: str | None = None
    effective_time: str | None = None
    expiration_time: str | None = None
    cancelled_time: str | None = None
    retroactive_time: str | None = None
    sub_organization_external_id: str | None = None
    is_claims_made: bool | None = None
    runoff_provision: str | None = None


class PolicyApiDisplaySchemaField(BaseModel):
    """Schema descriptor for a search result display column."""

    model_config = ConfigDict(extra="allow")

    id: str
    desc: str
    type: Literal["string", "date", "select"] | str


class PolicyApiSearchResult(BaseModel):
    """Individual search result item containing display values and retrieval token."""

    model_config = ConfigDict(extra="allow")

    display_fields: dict[str, Any]
    retrieval_token: str


class PolicyApiSearchResponse(BaseModel):
    """Response model for the GET /policies/search endpoint."""

    model_config = ConfigDict(extra="allow")

    total_results: int
    display_schema: list[PolicyApiDisplaySchemaField]
    results: list[PolicyApiSearchResult]
