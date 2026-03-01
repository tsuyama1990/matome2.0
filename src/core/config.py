import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Central configuration managed via environment variables."""

    # Provide defaults to safely load tests when not set
    openrouter_api_key: str = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    pinecone_api_key: str = Field(default_factory=lambda: os.getenv("PINECONE_API_KEY", ""))

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


settings = AppSettings()
