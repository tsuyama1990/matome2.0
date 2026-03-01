from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    OPENROUTER_API_KEY: str
    VECTOR_DB_URL: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
