import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core import constants


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


class LLMSettings(BaseModel):
    """Configuration specific to LLM interactions."""
    api_key: SecretStr = Field(default=SecretStr(""))
    text_fast_model: str = Field(default_factory=lambda: _defaults.get("text_fast_model", constants.DEFAULT_TEXT_FAST_MODEL))
    text_reasoning_model: str = Field(default_factory=lambda: _defaults.get("text_reasoning_model", constants.DEFAULT_TEXT_REASONING_MODEL))
    multimodal_model: str = Field(default_factory=lambda: _defaults.get("multimodal_model", constants.DEFAULT_MULTIMODAL_MODEL))
    base_url: HttpUrl | str = Field(default_factory=lambda: _defaults.get("openrouter_base_url", constants.DEFAULT_OPENROUTER_BASE_URL))
    timeout: float = Field(default_factory=lambda: _defaults.get("llm_timeout", constants.DEFAULT_LLM_TIMEOUT))


class VectorStoreSettings(BaseModel):
    """Configuration specific to Vector Database."""
    api_key: SecretStr = Field(default=SecretStr(""))
    index_name: str = Field(default_factory=lambda: _defaults.get("pinecone_index_name", constants.DEFAULT_PINECONE_INDEX_NAME))


class StorageSettings(BaseModel):
    """Configuration specific to storage backends."""
    base_dir: str = Field(default_factory=lambda: _defaults.get("storage_base_dir", constants.DEFAULT_STORAGE_BASE_DIR))


class AppSettings(BaseSettings):
    """Central configuration managed via environment variables."""

    # Provide flattened aliases via aliases for backwards compatibility with tests and envs
    # Pydantic BaseSettings can parse env vars directly into nested models using __ delimiter
    llm: LLMSettings = Field(default_factory=LLMSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)

    # We retain flat fields mapping to environment variables and validate in post_init
    openrouter_api_key: SecretStr = Field(default=SecretStr(""))
    pinecone_api_key: SecretStr = Field(default=SecretStr(""))

    # We maintain these for backward compatibility with tests
    text_fast_model: str = Field(default_factory=lambda: _defaults.get("text_fast_model", constants.DEFAULT_TEXT_FAST_MODEL))
    text_reasoning_model: str = Field(default_factory=lambda: _defaults.get("text_reasoning_model", constants.DEFAULT_TEXT_REASONING_MODEL))
    multimodal_model: str = Field(default_factory=lambda: _defaults.get("multimodal_model", constants.DEFAULT_MULTIMODAL_MODEL))
    openrouter_base_url: HttpUrl | str = Field(default_factory=lambda: _defaults.get("openrouter_base_url", constants.DEFAULT_OPENROUTER_BASE_URL))
    pinecone_index_name: str = Field(default_factory=lambda: _defaults.get("pinecone_index_name", constants.DEFAULT_PINECONE_INDEX_NAME))
    storage_base_dir: str = Field(default_factory=lambda: _defaults.get("storage_base_dir", constants.DEFAULT_STORAGE_BASE_DIR))
    llm_timeout: float = Field(default_factory=lambda: _defaults.get("llm_timeout", constants.DEFAULT_LLM_TIMEOUT))

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", env_nested_delimiter="__"
    )

    def model_post_init(self, __context: Any) -> None:
        """Automatically checks validation upon startup correctly."""
        # Synchronize flat env fields into compositional structure
        if self.openrouter_api_key.get_secret_value():
            self.llm.api_key = self.openrouter_api_key
        if self.pinecone_api_key.get_secret_value():
            self.vector_store.api_key = self.pinecone_api_key

        self.llm.text_fast_model = self.text_fast_model
        self.llm.text_reasoning_model = self.text_reasoning_model
        self.llm.multimodal_model = self.multimodal_model
        self.llm.base_url = self.openrouter_base_url
        self.llm.timeout = self.llm_timeout

        self.vector_store.index_name = self.pinecone_index_name
        self.storage.base_dir = self.storage_base_dir

        self.validate_keys()

    def validate_keys(self) -> None:
        """Validates that critical API keys are present."""
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
