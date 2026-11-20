from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(description="Standard error code from error catalogue")
    message: str = Field(description="Human-readable description of the error")
    details: dict[str, Any] | list[Any] | None = Field(
        default=None,
        description="Optional safe context details without sensitive info",
    )


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ErrorDetail
    correlation_id: str | None = Field(default=None, description="Request correlation identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when the error occurred",
    )
