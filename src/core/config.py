import os
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.constants import (
    DEFAULT_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    DEFAULT_CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS,
    DEFAULT_ENVIRONMENT,
    DEFAULT_RETRY_DELAY_SECONDS,
    DEFAULT_RETRY_MAX_ATTEMPTS,
    DEFAULT_VDB_BATCH_SIZE,
)


class AppSettings(BaseSettings):
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", DEFAULT_ENVIRONMENT))
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
        default_factory=lambda: int(os.getenv("RETRY_DELAY_SECONDS", DEFAULT_RETRY_DELAY_SECONDS)),
        ge=0,
    )
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(
        default_factory=lambda: int(
            os.getenv(
                "CIRCUIT_BREAKER_FAILURE_THRESHOLD", DEFAULT_CIRCUIT_BREAKER_FAILURE_THRESHOLD
            )
        ),
        ge=1,
    )
    CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS: int = Field(
        default_factory=lambda: int(
            os.getenv(
                "CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS",
                DEFAULT_CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS,
            )
        ),
        ge=1,
    )
    MAX_KEEPALIVE_CONNECTIONS: int = Field(
        default_factory=lambda: int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "20")), ge=1
    )
    MAX_CONNECTIONS: int = Field(
        default_factory=lambda: int(os.getenv("MAX_CONNECTIONS", "100")), ge=1
    )
    ALLOWED_DOCUMENT_DIR: Path = Field(...)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def validate_configuration_consistency(self) -> "AppSettings":
        """Cross field validation for configuration settings."""
        if self.VDB_BATCH_SIZE < 1:
            msg = "VDB_BATCH_SIZE must be greater than 0"
            raise ValueError(msg)
        if self.RETRY_MAX_ATTEMPTS > 10 and self.RETRY_DELAY_SECONDS > 10:
            msg = (
                "Retry mechanism is configured too aggressively (Max Attempts > 10 and Delay > 10s)"
            )
            raise ValueError(msg)

        allowed_dir = self.ALLOWED_DOCUMENT_DIR.resolve()
        if not allowed_dir.exists() or not allowed_dir.is_dir():
            msg = f"ALLOWED_DOCUMENT_DIR must exist and be a directory: {allowed_dir}"
            raise ValueError(msg)

        import os

        if not os.access(allowed_dir, os.R_OK | os.W_OK):
            msg = f"ALLOWED_DOCUMENT_DIR must be readable and writable: {allowed_dir}"
            raise ValueError(msg)

        return self
