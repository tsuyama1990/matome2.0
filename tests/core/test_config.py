import pytest
from pydantic import ValidationError

from src.core.config import AppSettings


def test_app_settings_missing_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("VECTOR_DB_URL", raising=False)
    monkeypatch.delenv("ALLOWED_DOCUMENT_DIR", raising=False)
    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)  # type: ignore[call-arg]


def test_app_settings_inconsistent_retry_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory
) -> None:
    import uuid

    mock_key = uuid.uuid4().hex
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_key)
    monkeypatch.setenv("VECTOR_DB_URL", "http://test-url.local")
    monkeypatch.setenv("ALLOWED_DOCUMENT_DIR", str(tmp_path))
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "11")
    monkeypatch.setenv("RETRY_DELAY_SECONDS", "11")

    with pytest.raises(ValidationError, match="Retry mechanism is configured too aggressively"):
        AppSettings(_env_file=None)  # type: ignore[call-arg]


def test_app_settings_valid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory
) -> None:
    import uuid

    mock_key = uuid.uuid4().hex
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_key)
    monkeypatch.setenv("VECTOR_DB_URL", "http://localhost:8080")
    monkeypatch.setenv("VDB_BATCH_SIZE", "100")
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "5")
    monkeypatch.setenv("ALLOWED_DOCUMENT_DIR", str(tmp_path))
    settings = AppSettings(_env_file=None)  # type: ignore[call-arg]
    assert mock_key == settings.OPENROUTER_API_KEY
    assert settings.VECTOR_DB_URL == "http://localhost:8080"
    assert settings.VDB_BATCH_SIZE == 100
    assert settings.RETRY_MAX_ATTEMPTS == 5
