"""Policy response and request schemas.

Fields are derived strictly from confirmed policy reference requirements.
Exact field types and JSON property names are marked TBC where unconfirmed.
Separate canonical entities for Policy Version, Insured, Limit, Deductible,
or Source Reference are excluded per instructions.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PolicyResponse(BaseModel):
    """Policy response schema using strictly confirmed fields (types and property names: TBC)."""

    model_config = ConfigDict(extra="ignore")

    policy_number: Any = Field(default="TBC", description="Policy Number (TBC)")
    effective_date: Any = Field(default="TBC", description="Effective Date (TBC)")
    expiration_date: Any = Field(default="TBC", description="Expiration Date (TBC)")
    currency: Any = Field(default="TBC", description="Currency (TBC)")
    policy_state: Any = Field(default="TBC", description="Policy State (TBC)")
    policy_holder_company: Any = Field(default="TBC", description="Policy Holder Company (TBC)")
    uw_region: Any = Field(default="TBC", description="UW Region (TBC)")
    writing_company: Any = Field(default="TBC", description="Writing Company (TBC)")
    booked_as_value: Any = Field(default="TBC", description="Booked As Value (TBC)")
    product_line_uw_area: Any = Field(default="TBC", description="Product Line/UW Area (TBC)")
    product_line_subtype: Any = Field(default="TBC", description="Product Line Subtype (TBC)")
    section_code_name: Any = Field(default="TBC", description="Section Code Name (TBC)")
    asl: Any = Field(default="TBC", description="ASL (TBC)")
    class_code_iso: Any = Field(default="TBC", description="Class Code (ISO) (TBC)")
    subline_iso: Any = Field(default="TBC", description="Subline (ISO) (TBC)")
    deductible_codes_iso: Any = Field(default="TBC", description="Deductible Codes (ISO) (TBC)")
    primary_involved_location_detail_iso: Any = Field(
        default="TBC", description="Primary Involved Location Detail (ISO) (TBC)"
    )

    # Document information shown in screenshot (Coverage used instead of Line)
    coverage_exposure: Any = Field(default="TBC", description="Coverage/Exposure (TBC)")
    limits_retentions: Any = Field(default="TBC", description="Limits, Retentions (TBC)")
    dates_retro_tail: Any = Field(default="TBC", description="Dates, Retro Tail (TBC)")


class PolicySearchRequest(BaseModel):
    """Policy search request payload (criteria fields: TBC)."""

    model_config = ConfigDict(extra="ignore")

    criteria: Any = Field(default="TBC", description="Search criteria (TBC)")


class CoverageResponse(BaseModel):
    """Policy coverage response payload (fields: TBC)."""

    model_config = ConfigDict(extra="ignore")

    coverage_exposure: Any = Field(default="TBC", description="Coverage/Exposure (TBC)")
    limits_retentions: Any = Field(default="TBC", description="Limits, Retentions (TBC)")
    dates_retro_tail: Any = Field(default="TBC", description="Dates, Retro Tail (TBC)")
