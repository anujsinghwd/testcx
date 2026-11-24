"""Application configuration settings for Policy Search Service."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BHSI Policy Search Integration"
    environment: str = "development"

    # Inbound API key authentication for Five Sigma
    api_key: str = Field(
        default="test-api-key",
        alias="API_KEY",
        description="Default API key for inbound Five Sigma authentication",
    )
    five_sigma_inbound_api_key: str = Field(
        default="test-five-sigma-key",
        alias="FIVE_SIGMA_INBOUND_API_KEY",
        description="Configured Five Sigma inbound API key",
    )

    # MySQL Database configuration
    mysql_host: str = Field(
        default="localhost",
        alias="MYSQL_HOST",
        description="MySQL server host",
    )
    mysql_port: int = Field(
        default=3306,
        alias="MYSQL_PORT",
        description="MySQL server port",
    )
    mysql_database: str = Field(
        default="policy_integration",
        alias="MYSQL_DATABASE",
        description="MySQL database name for Policy Integration",
    )
    mysql_user: str = Field(
        default="policy_user",
        alias="MYSQL_USER",
        description="MySQL database username",
    )
    mysql_password: str = Field(
        default="password",
        alias="MYSQL_PASSWORD",
        description="MySQL database password",
    )
    database_url: str | None = Field(
        default=None,
        alias="DATABASE_URL",
        description="Complete database connection URL (overrides individual parameters if set)",
    )

    def get_database_url(self) -> str:
        """Returns the configured database URL or constructs a MySQL connection string."""
        if self.database_url:
            return self.database_url
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@"
            f"{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()
