import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.constants import (
    DEFAULT_ALLOWED_DOCUMENT_DIR,
    DEFAULT_ENVIRONMENT,
    DEFAULT_RETRY_DELAY_SECONDS,
    DEFAULT_RETRY_MAX_ATTEMPTS,
    DEFAULT_VDB_BATCH_SIZE,
)


class AppSettings(BaseSettings):
    ENVIRONMENT: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", DEFAULT_ENVIRONMENT)
    )
    OPENROUTER_API_KEY: str = Field(..., min_length=1)
    VECTOR_DB_URL: str = Field(..., min_length=1)
    VDB_BATCH_SIZE: int = Field(
        default_factory=lambda: int(os.getenv("VDB_BATCH_SIZE", DEFAULT_VDB_BATCH_SIZE)), ge=1
    )
    RETRY_MAX_ATTEMPTS: int = Field(
        default_factory=lambda: int(os.getenv("RETRY_MAX_ATTEMPTS", DEFAULT_RETRY_MAX_ATTEMPTS)),
        ge=1,
    )
    RETRY_DELAY_SECONDS: int = Field(
        default_factory=lambda: int(
            os.getenv("RETRY_DELAY_SECONDS", DEFAULT_RETRY_DELAY_SECONDS)
        ),
        ge=0,
    )
    ALLOWED_DOCUMENT_DIR: Path = Field(
        default_factory=lambda: Path(
            os.getenv("ALLOWED_DOCUMENT_DIR", DEFAULT_ALLOWED_DOCUMENT_DIR)
        )
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
