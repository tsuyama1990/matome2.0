import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, SecretStr, field_validator
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


class LLMSettings(BaseModel):
    """Configuration specific to LLM interactions."""

    provider: Literal["openrouter", "openai", "anthropic"] = Field(default="openrouter")
    api_key: SecretStr = Field(default=SecretStr(""))
    text_fast_model: str = Field(
        default_factory=lambda: _defaults.get("text_fast_model", "google/gemini-2.5-flash")
    )
    text_reasoning_model: str = Field(
        default_factory=lambda: _defaults.get("text_reasoning_model", "deepseek/deepseek-reasoner")
    )
    multimodal_model: str = Field(
        default_factory=lambda: _defaults.get("multimodal_model", "google/gemini-2.5-pro")
    )
    base_url: HttpUrl | str = Field(
        default_factory=lambda: _defaults.get(
            "openrouter_base_url", "https://openrouter.ai/api/v1/chat/completions"
        )
    )
    timeout: float = Field(default_factory=lambda: _defaults.get("llm_timeout", 30.0))
    max_retries: int = Field(default_factory=lambda: _defaults.get("llm_max_retries", 3))
    base_delay: float = Field(default_factory=lambda: _defaults.get("llm_base_delay", 1.0))


class VectorStoreSettings(BaseModel):
    """Configuration specific to Vector Database."""

    api_key: SecretStr = Field(default=SecretStr(""))
    index_name: str = Field(
        default_factory=lambda: _defaults.get("pinecone_index_name", "matome-index")
    )
    max_retries: int = Field(default_factory=lambda: _defaults.get("vector_store_max_retries", 3))
    base_delay: float = Field(default_factory=lambda: _defaults.get("vector_store_base_delay", 1.0))
    batch_size: int = Field(default_factory=lambda: _defaults.get("vector_store_batch_size", 100))
    max_batch_size: int = Field(
        default_factory=lambda: _defaults.get("vector_store_max_batch_size", 10000)
    )


class StorageSettings(BaseModel):
    """Configuration specific to storage backends."""

    base_dir: str = Field(default_factory=lambda: _defaults.get("storage_base_dir", "./data"))
    max_upload_size: int = Field(
        default_factory=lambda: _defaults.get("storage_max_upload_size", 10 * 1024 * 1024)
    )


class AppSettings(BaseSettings):
    """Central configuration managed via environment variables."""

    environment: Literal["dev", "staging", "prod"] = Field(default="dev")
    llm: LLMSettings = Field(default_factory=LLMSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", env_nested_delimiter="__"
    )


    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v: Any) -> str:
        """Ensures environment falls back cleanly if misconfigured."""
        if isinstance(v, str) and v.lower() in ("dev", "staging", "prod"):
            return v.lower()
        return "dev"

    def model_post_init(self, __context: Any) -> None:
        """Automatically checks validation upon startup correctly."""
        if self.environment == "prod" and (
            not self.llm.api_key.get_secret_value()
            or not self.vector_store.api_key.get_secret_value()
        ):
            msg = "Production environment requires both OPENROUTER_API_KEY and PINECONE_API_KEY."
            raise ValueError(msg)
        if not self.llm.api_key.get_secret_value():
            msg = (
                "OPENROUTER_API_KEY environment variable is not set or is empty. "
                "Without this key, the OpenRouter LLM generation services will be unavailable."
            )
            raise ValueError(msg)
        if not self.vector_store.api_key.get_secret_value():
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
