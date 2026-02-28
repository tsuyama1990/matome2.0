import pytest
from pydantic import ValidationError

from src.domain_models.config import AppSettings


def test_valid_app_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("VECTOR_DB_URL", "http://test-db")

    settings = AppSettings()  # type: ignore[call-arg]

    assert settings.openrouter_api_key == "test_key"
    assert settings.vector_db_url == "http://test-db"
    assert settings.environment == "development"


def test_missing_required_settings_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("VECTOR_DB_URL", raising=False)

    with pytest.raises(ValidationError):
        AppSettings()  # type: ignore[call-arg]


def test_empty_string_raises_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("VECTOR_DB_URL", "")

    with pytest.raises(ValidationError):
        AppSettings()  # type: ignore[call-arg]
