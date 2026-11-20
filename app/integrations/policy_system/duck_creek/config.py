"""Configuration loader for Duck Creek policy system adapter."""

from typing import Any


class DuckCreekConfigLoader:
    """Loads configuration and connection parameters for Duck Creek."""

    def __init__(self) -> None:
        pass

    def load_config(self) -> dict[str, Any]:
        """Load Duck Creek configuration settings.

        Connection URLs, authentication credentials, and timeout settings: TBC.
        """
        return {
            "base_url": "TBC",
            "api_key": "TBC",
            "timeout_seconds": "TBC",
        }
