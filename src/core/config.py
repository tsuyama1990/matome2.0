import os

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Central configuration managed via environment variables."""

    # Provide defaults to safely load tests when not set
    openrouter_api_key: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("OPENROUTER_API_KEY", "NOT_SET"))
    )
    pinecone_api_key: SecretStr = Field(
        default_factory=lambda: SecretStr(os.getenv("PINECONE_API_KEY", "NOT_SET"))
    )

    text_fast_model: str = Field(
        default_factory=lambda: os.getenv("TEXT_FAST_MODEL", "google/gemini-2.5-flash")
    )
    text_reasoning_model: str = Field(
        default_factory=lambda: os.getenv("TEXT_REASONING_MODEL", "deepseek/deepseek-reasoner")
    )
    multimodal_model: str = Field(
        default_factory=lambda: os.getenv("MULTIMODAL_MODEL", "google/gemini-2.5-pro")
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def validate_keys(self) -> None:
        """Validates that critical API keys are present."""
        if self.openrouter_api_key.get_secret_value() == "NOT_SET":
            msg = "OPENROUTER_API_KEY environment variable is not set or is empty."
            raise ValueError(msg)
        if self.pinecone_api_key.get_secret_value() == "NOT_SET":
            msg = "PINECONE_API_KEY environment variable is not set or is empty."
            raise ValueError(msg)


settings = AppSettings()
