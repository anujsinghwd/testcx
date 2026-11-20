"""Application configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BHSI Integration"
    environment: str = "development"

    # Duck Creek API configuration - details TBC
    duck_creek_base_url: str = Field(
        default="TBC",
        alias="DUCK_CREEK_BASE_URL",
        description="Base URL for Duck Creek API (TBC)",
    )
    duck_creek_api_key: str = Field(
        default="TBC",
        alias="DUCK_CREEK_API_KEY",
        description="API Key for Duck Creek API (TBC)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
