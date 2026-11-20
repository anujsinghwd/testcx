from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import BaseIntegrationError
from app.core.logger import get_logger, redact_sensitive_data
from app.schemas.errors import ErrorDetail, ErrorResponse

logger = get_logger("app.core.error_handlers")


def _get_correlation_id(request: Request) -> str | None:
    return getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID")


async def integration_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, BaseIntegrationError):
        return await unhandled_exception_handler(request, exc)

    correlation_id = _get_correlation_id(request)
    safe_details = redact_sensitive_data(exc.details) if exc.details else None

    logger.warning(
        "Integration error occurred: code=%s, status=%s, message=%s, correlation_id=%s, details=%s",
        exc.code,
        exc.status_code,
        exc.message,
        correlation_id,
        safe_details,
    )

    error_response = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=safe_details,
        ),
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        return await unhandled_exception_handler(request, exc)

    correlation_id = _get_correlation_id(request)
    logger.info(
        "Validation error on %s %s: errors=%s, correlation_id=%s",
        request.method,
        request.url.path,
        exc.errors(),
        correlation_id,
    )

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=jsonable_encoder(exc.errors()),
        ),
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump(mode="json"),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = _get_correlation_id(request)
    logger.exception(
        "Unhandled server error on %s %s: correlation_id=%s",
        request.method,
        request.url.path,
        correlation_id,
    )

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal error occurred.",
            details=None,
        ),
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Registers centralized exception handlers onto the FastAPI application."""
    app.add_exception_handler(BaseIntegrationError, integration_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
