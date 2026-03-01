from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Central configuration managed via environment variables."""

    # Explicit mapping and environment loading via Pydantic model configuration
    openrouter_api_key: SecretStr = Field(default=SecretStr("UNCONFIGURED_API_KEY"))
    pinecone_api_key: SecretStr = Field(default=SecretStr("UNCONFIGURED_API_KEY"))

    text_fast_model: str = Field(default="google/gemini-2.5-flash")
    text_reasoning_model: str = Field(default="deepseek/deepseek-reasoner")
    multimodal_model: str = Field(default="google/gemini-2.5-pro")

    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1/chat/completions")
    pinecone_index_name: str = Field(default="matome-index")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", env_nested_delimiter="__"
    )

    def validate_keys(self) -> None:
        """Validates that critical API keys are present."""
        if self.openrouter_api_key.get_secret_value() == "UNCONFIGURED_API_KEY":
            msg = "OPENROUTER_API_KEY environment variable is not set or is empty."
            raise ValueError(msg)
        if self.pinecone_api_key.get_secret_value() == "UNCONFIGURED_API_KEY":
            msg = "PINECONE_API_KEY environment variable is not set or is empty."
            raise ValueError(msg)


settings = AppSettings()
