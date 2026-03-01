import pytest
from pydantic import ValidationError

from src.core.config import AppSettings


def test_app_settings_missing_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("VECTOR_DB_URL", raising=False)
    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)  # type: ignore[call-arg]

def test_app_settings_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("VECTOR_DB_URL", "http://localhost:8080")
    settings = AppSettings(_env_file=None)  # type: ignore[call-arg]
    assert settings.OPENROUTER_API_KEY == "test_key"
    assert settings.VECTOR_DB_URL == "http://localhost:8080"
