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


class AuthenticationError(BaseIntegrationError):
    """Raised when an inbound request fails API key authentication."""

    def __init__(
        self,
        message: str = "Invalid or missing API key",
        code: str = "UNAUTHORIZED",
        status_code: int = 401,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            details=details,
        )


class PolicyNotFoundError(BaseIntegrationError):
    """Raised when a requested policy or policy retrieval token is not found."""

    def __init__(
        self,
        message: str = "Policy not found",
        code: str = "NOT_FOUND",
        status_code: int = 404,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            details=details,
        )


class MultiplePoliciesFoundError(BaseIntegrationError):
    """Raised when multiple matching policies are found where a unique policy is required."""

    def __init__(
        self,
        message: str = "Multiple matching policies found",
        code: str = "MULTIPLE_MATCHES",
        status_code: int = 409,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
            details=details,
        )


class DatabaseError(BaseIntegrationError):
    """Raised when a repository or database operation fails."""

    def __init__(
        self,
        message: str = "Database operation failed",
        code: str = "DATABASE_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status_code,
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
