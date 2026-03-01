import pytest
from pydantic import ValidationError

from src.core.config import AppSettings


def test_app_settings_missing_required() -> None:
    with pytest.raises(ValidationError):
        # Missing required parameters
        AppSettings()  # type: ignore[call-arg]


def test_app_settings_defaults(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory
) -> None:
    # Ensure variables have their appropriate default values if not specifically configured.
    import uuid

    mock_key = uuid.uuid4().hex

    # We ONLY set required fields, the rest must fall back
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_key)
    monkeypatch.setenv("VECTOR_DB_URL", "http://test-url.local")
    monkeypatch.setenv("ALLOWED_DOCUMENT_DIR", str(tmp_path))

    settings = AppSettings(_env_file=None)  # type: ignore[call-arg]
    assert settings.VDB_BATCH_SIZE == 1000
    assert settings.RETRY_MAX_ATTEMPTS == 3
    assert settings.RETRY_DELAY_SECONDS == 1
    assert settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD == 5
    assert settings.CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS == 30
    assert settings.MAX_KEEPALIVE_CONNECTIONS == 20
    assert settings.MAX_CONNECTIONS == 100


def test_app_settings_inconsistent_retry_config(tmp_path: pytest.TempPathFactory) -> None:
    from tests.conftest import TestConfigFactory

    settings = TestConfigFactory.create(str(tmp_path))
    settings.RETRY_MAX_ATTEMPTS = 11
    settings.RETRY_DELAY_SECONDS = 11
    with pytest.raises(ValidationError, match="Retry mechanism is configured too aggressively"):
        # Pydantic validates on init, so we must trigger validation
        AppSettings(**settings.model_dump())


def test_app_settings_valid(app_settings: AppSettings) -> None:
    assert app_settings.OPENROUTER_API_KEY is not None
    assert app_settings.VECTOR_DB_URL == "http://test-url.local"
    assert app_settings.VDB_BATCH_SIZE == 100
    assert app_settings.RETRY_MAX_ATTEMPTS == 3
