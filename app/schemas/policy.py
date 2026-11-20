from datetime import date
from decimal import Decimal
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceReference(BaseModel):
    """Reference tracking the source system record for a policy or coverage."""

    model_config = ConfigDict(extra="forbid")

    system: str = Field(
        default="Five Sigma",
        description="Originating source system name",
    )
    source_id: str = Field(description="Unique record identifier in the source system")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Source system metadata")


class Deductible(BaseModel):
    """Policy or coverage deductible specification."""

    model_config = ConfigDict(extra="forbid")

    deductible_id: str | None = Field(
        default=None, description="Unique identifier for the deductible"
    )
    name: str = Field(description="Name or category of deductible")
    amount: Decimal = Field(
        ge=Decimal("0.00"), description="Deductible monetary amount, non-negative"
    )
    currency: str = Field(default="USD", max_length=3, description="ISO currency code")
    description: str | None = Field(default=None, description="Deductible description")


class Limit(BaseModel):
    """Monetary limit applied to a coverage or policy."""

    model_config = ConfigDict(extra="forbid")

    limit_id: str | None = Field(default=None, description="Unique identifier for the limit")
    name: str = Field(description="Limit type or name")
    amount: Decimal = Field(ge=Decimal("0.00"), description="Limit monetary amount, non-negative")
    currency: str = Field(default="USD", max_length=3, description="ISO currency code")
    description: str | None = Field(default=None, description="Limit description")


class Coverage(BaseModel):
    """Insurance coverage object with nested limits and deductibles."""

    model_config = ConfigDict(extra="forbid")

    coverage_id: str | None = Field(default=None, description="Unique identifier for coverage")
    code: str = Field(description="Standard coverage code (e.g., BI, PD, COMP)")
    name: str = Field(description="Descriptive coverage name")
    effective_date: date | None = Field(
        default=None, description="Effective date for this coverage"
    )
    expiration_date: date | None = Field(
        default=None, description="Expiration date for this coverage"
    )
    status: str | None = Field(default="Active", description="Coverage status")
    limits: list[Limit] = Field(
        default_factory=list, description="Applicable limits for this coverage"
    )
    deductibles: list[Deductible] = Field(
        default_factory=list, description="Applicable deductibles for this coverage"
    )
    source_reference: SourceReference | None = Field(
        default=None, description="Source system tracking reference"
    )

    @model_validator(mode="after")
    def validate_coverage_dates(self) -> Self:
        if (
            self.effective_date
            and self.expiration_date
            and self.expiration_date < self.effective_date
        ):
            raise ValueError("Coverage expiration date cannot be earlier than effective date")
        return self


class Insured(BaseModel):
    """Insured party associated with a policy."""

    model_config = ConfigDict(extra="forbid")

    customer_id: str | None = Field(default=None, description="Unique customer ID from Five Sigma")
    name: str = Field(description="Full legal name of the insured")
    first_name: str | None = Field(default=None, description="First name")
    last_name: str | None = Field(default=None, description="Last name")
    email: str | None = Field(default=None, description="Contact email address")
    phone_number: str | None = Field(default=None, description="Contact phone number")
    type: str | None = Field(default="Primary", description="Insured type")


class PolicyVersion(BaseModel):
    """Policy version tracking."""

    model_config = ConfigDict(extra="forbid")

    version_id: str = Field(default="V1", description="Unique identifier for policy version")
    effective_date: date | None = Field(default=None, description="Effective date of this version")
    expiration_date: date | None = Field(
        default=None, description="Expiration date of this version"
    )
    status: str = Field(default="Active", description="Version status")
    description: str | None = Field(default=None, description="Summary of changes in this version")

    @model_validator(mode="after")
    def validate_version_dates(self) -> Self:
        if (
            self.effective_date
            and self.expiration_date
            and self.expiration_date < self.effective_date
        ):
            raise ValueError("Policy version expiration date cannot be earlier than effective date")
        return self


class Policy(BaseModel):
    """Canonical Policy business object."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str = Field(description="Policy identifier (e.g. POL12345)")
    customer_id: str | None = Field(
        default=None, description="Associated customer ID (e.g. CUST001)"
    )
    insured_name: str | None = Field(default=None, description="Insured name (e.g. John Smith)")
    status: str = Field(description="Policy status (e.g., Active, Expired, Cancelled)")
    effective_date: date = Field(description="Policy effective date")
    expiration_date: date = Field(description="Policy expiration date")
    sub_organization: str | None = Field(default=None, description="Sub organization (e.g. ORGCA)")
    line_of_business: str | None = Field(default=None, description="Line of business (e.g. Auto)")
    vin: str | None = Field(
        default=None, description="Vehicle identification number (e.g. VIN123456789)"
    )
    current_version: PolicyVersion | None = Field(default=None, description="Active policy version")
    insured_parties: list[Insured] = Field(
        default_factory=list, description="Insured parties under the policy"
    )
    coverages: list[Coverage] = Field(
        default_factory=list, description="Coverages under the policy"
    )
    total_premium: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        description="Total policy gross premium, non-negative",
    )
    source_reference: SourceReference | None = Field(
        default=None, description="Source system origin reference"
    )

    @model_validator(mode="after")
    def validate_policy_dates(self) -> Self:
        if self.expiration_date < self.effective_date:
            raise ValueError("Policy expiration date cannot be earlier than effective date")
        return self


class PolicySearchRequest(BaseModel):
    """Request payload for querying policies by criteria."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str | None = Field(default=None, description="Exact or partial policy number")
    insured_name: str | None = Field(default=None, description="Name of the insured entity")
    customer_id: str | None = Field(default=None, description="Customer ID filter")
    line_of_business: str | None = Field(default=None, description="Line of business filter")
    status: str | None = Field(default=None, description="Policy status filter")
    vin: str | None = Field(default=None, description="Vehicle identification number filter")

    @model_validator(mode="after")
    def validate_at_least_one_criterion(self) -> Self:
        if not any(
            [
                self.policy_number,
                self.insured_name,
                self.customer_id,
                self.line_of_business,
                self.status,
                self.vin,
            ]
        ):
            raise ValueError("At least one search criterion must be provided.")
        return self


class PolicySearchResponse(BaseModel):
    """Response payload containing matching canonical policies."""

    model_config = ConfigDict(extra="forbid")

    policies: list[Policy] = Field(default_factory=list, description="List of matching policies")
    total_count: int = Field(ge=0, description="Total number of matching policies returned")


class PolicyDetailResponse(BaseModel):
    """Response payload returning detailed canonical policy information."""

    model_config = ConfigDict(extra="forbid")

    policy: Policy = Field(description="Detailed canonical policy object")


class PolicyCoveragesResponse(BaseModel):
    """Response payload returning coverages, limits, and deductibles for a policy."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str = Field(description="Policy number")
    coverages: list[Coverage] = Field(
        default_factory=list, description="List of coverages under the policy"
    )
    total_count: int = Field(ge=0, description="Total count of coverages returned")
