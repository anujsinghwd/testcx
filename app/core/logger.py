import logging
import re
from typing import Any

SENSITIVE_KEYS: set[str] = {
    "api_key",
    "apikey",
    "authorization",
    "password",
    "secret",
    "token",
    "ssn",
    "tax_id",
}

MASK_VALUE = "******"


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redacts sensitive keys from dictionaries, lists, and strings."""
    if isinstance(data, dict):
        redacted_dict: dict[str, Any] = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                redacted_dict[key] = MASK_VALUE
            else:
                redacted_dict[key] = redact_sensitive_data(value)
        return redacted_dict
    if isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    if isinstance(data, str):
        # Redact Bearer tokens in headers/strings
        return re.sub(r"Bearer\s+([A-Za-z0-9\-_\.]+)", "Bearer ******", data)
    return data


def setup_logging(level: int = logging.INFO) -> None:
    """Configures centralized structured logging for the application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )


def get_logger(name: str) -> logging.Logger:
    """Returns a module logger instance."""
    return logging.getLogger(name)
