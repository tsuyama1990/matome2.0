import json
from pathlib import Path
from typing import Any

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_defaults() -> dict[str, Any]:
    default_path = Path("config.json")
    if default_path.exists():
        try:
            res = json.loads(default_path.read_text())
            return dict(res) if isinstance(res, dict) else {}
        except Exception:
            return {}
    return {}

_defaults = _load_defaults()

class ConfigFactory:
    """Factory to create and configure AppSettings instances."""

    @staticmethod
    def create_settings(**kwargs: Any) -> "AppSettings":
        """Initializes and returns an AppSettings instance."""
        return AppSettings(**kwargs)


class AppSettings(BaseSettings):
    """Central configuration managed via environment variables."""

    # Explicit mapping and environment loading via Pydantic model configuration
    openrouter_api_key: SecretStr = Field(default=SecretStr(""))
    pinecone_api_key: SecretStr = Field(default=SecretStr(""))

    text_fast_model: str = Field(default_factory=lambda: _defaults.get("text_fast_model", "google/gemini-2.5-flash"))
    text_reasoning_model: str = Field(default_factory=lambda: _defaults.get("text_reasoning_model", "deepseek/deepseek-reasoner"))
    multimodal_model: str = Field(default_factory=lambda: _defaults.get("multimodal_model", "google/gemini-2.5-pro"))

    openrouter_base_url: HttpUrl | str = Field(default_factory=lambda: _defaults.get("openrouter_base_url", "https://openrouter.ai/api/v1/chat/completions"))
    pinecone_index_name: str = Field(default_factory=lambda: _defaults.get("pinecone_index_name", "matome-index"))
    storage_base_dir: str = Field(default_factory=lambda: _defaults.get("storage_base_dir", "./data"))
    llm_timeout: float = Field(default_factory=lambda: _defaults.get("llm_timeout", 30.0))

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", env_nested_delimiter="__"
    )

    def model_post_init(self, __context: Any) -> None:
        """Automatically checks validation upon startup correctly."""
        self.validate_keys()

    def validate_keys(self) -> None:
        """Validates that critical API keys are present."""
        if not self.openrouter_api_key.get_secret_value():
            msg = (
                "OPENROUTER_API_KEY environment variable is not set or is empty. "
                "Without this key, the OpenRouter LLM generation services will be unavailable."
            )
            raise ValueError(msg)
        if not self.pinecone_api_key.get_secret_value():
            msg = (
                "PINECONE_API_KEY environment variable is not set or is empty. "
                "Without this key, the Pinecone Vector Store semantic searches will be unavailable."
            )
            raise ValueError(msg)


# For testing without loading settings right away, we defer initialization or catch the error
# based on when the app requires the actual configurations.
# Settings initialization is deferred to the container creation so it doesn't break CI immediately
# on imports before tests can setup environments.
# To keep previous test logic valid we remove the global settings instance here and instantiate it where needed.
