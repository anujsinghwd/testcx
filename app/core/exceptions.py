from typing import Any


class BaseIntegrationError(Exception):
    """Base exception for all integration and domain errors."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


# Backward compatibility alias
BaseIntegrationException = BaseIntegrationError


class PolicyNotFoundError(BaseIntegrationError):
    """Raised when a requested policy or policy version is not found."""

    def __init__(
        self,
        message: str = "Policy not found",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class MultiplePoliciesFoundError(BaseIntegrationError):
    """Raised when multiple matching policies are found where a unique policy is required."""

    def __init__(
        self,
        message: str = "Multiple matching policies found",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="MULTIPLE_MATCHES",
            status_code=409,
            details=details,
        )


class PASUnavailableError(BaseIntegrationError):
    """Raised when the Policy Administration System (Duck Creek) is down or unreachable."""

    def __init__(
        self,
        message: str = "Policy Administration System is currently unavailable",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="PAS_UNAVAILABLE",
            status_code=503,
            details=details,
        )


class PASTimeoutError(BaseIntegrationError):
    """Raised when the Policy Administration System request times out."""

    def __init__(
        self,
        message: str = "Policy Administration System request timed out",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="TIMEOUT",
            status_code=504,
            details=details,
        )


class PolicyMappingError(BaseIntegrationError):
    """Raised when provider response data cannot be mapped into the canonical schema."""

    def __init__(
        self,
        message: str = "Failed to map policy data from provider response",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="MAPPING_ERROR",
            status_code=502,
            details=details,
        )
