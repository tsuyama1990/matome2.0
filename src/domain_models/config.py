from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """
    Application configuration settings, loaded from environment variables or .env.
    """

    openrouter_api_key: str = Field(..., min_length=1)
    vector_db_url: str = Field(..., min_length=1)
    environment: str = Field(default="development")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
