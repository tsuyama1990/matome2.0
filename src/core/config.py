from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    OPENROUTER_API_KEY: str = Field(..., min_length=1)
    VECTOR_DB_URL: str = Field(..., min_length=1)
    VDB_BATCH_SIZE: int = Field(default=1000, ge=1)
    RETRY_MAX_ATTEMPTS: int = Field(default=3, ge=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
