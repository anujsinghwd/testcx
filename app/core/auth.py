"""Inbound API key authentication for Five Sigma requests."""

from fastapi import Security
from fastapi.security.api_key import APIKeyHeader

from app.core.config import settings
from app.core.exceptions import AuthenticationError

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key_header: str | None = Security(API_KEY_HEADER),
) -> str:
    """Verifies the inbound X-API-Key header against configured API keys.

    Raises AuthenticationError (HTTP 401) if missing or invalid.
    """
    if not api_key_header:
        raise AuthenticationError(message="Missing required API key header: X-API-Key")

    valid_keys = {settings.api_key, settings.five_sigma_inbound_api_key}
    if api_key_header not in valid_keys:
        raise AuthenticationError(message="Invalid API key provided")

    return api_key_header
