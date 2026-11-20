from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Five Sigma BHSI Integration"
    environment: str = "development"

    # Five Sigma API configuration
    five_sigma_base_url: str = Field(
        default="",
        alias="FIVE_SIGMA_BASE_URL",
        description="Base URL for Five Sigma API",
    )
    five_sigma_api_key: str = Field(
        default="",
        alias="FIVE_SIGMA_API_KEY",
        description="API Key for Five Sigma API",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
