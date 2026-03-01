from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    OPENROUTER_API_KEY: str = Field(..., min_length=1)
    VECTOR_DB_URL: str = Field(..., min_length=1)
    VDB_BATCH_SIZE: int = Field(ge=1)
    RETRY_MAX_ATTEMPTS: int = Field(ge=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
