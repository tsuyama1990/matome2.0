import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    OPENROUTER_API_KEY: str = Field(..., min_length=1)
    VECTOR_DB_URL: str = Field(..., min_length=1)
    VDB_BATCH_SIZE: int = Field(default_factory=lambda: int(os.getenv("VDB_BATCH_SIZE", "1000")), ge=1)
    RETRY_MAX_ATTEMPTS: int = Field(default_factory=lambda: int(os.getenv("RETRY_MAX_ATTEMPTS", "3")), ge=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
