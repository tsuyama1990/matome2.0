import uuid

import pytest

from src.core.config import AppSettings


@pytest.fixture
def app_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory) -> AppSettings:
    """Provides a centralized, isolated configuration fixture for tests."""
    mock_key = uuid.uuid4().hex

    # Use monkeypatch to ensure isolation
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_key)
    monkeypatch.setenv("VECTOR_DB_URL", "http://test-url.local")
    monkeypatch.setenv("VDB_BATCH_SIZE", "100")
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("RETRY_DELAY_SECONDS", "0")
    monkeypatch.setenv("ALLOWED_DOCUMENT_DIR", str(tmp_path))
    monkeypatch.setenv("MAX_KEEPALIVE_CONNECTIONS", "5")
    monkeypatch.setenv("MAX_CONNECTIONS", "10")

    return AppSettings(_env_file=None)  # type: ignore[call-arg]
