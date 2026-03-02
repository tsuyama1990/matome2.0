import pytest

from src.core.config import AppSettings


def test_settings_initialization(test_config: AppSettings) -> None:
    """Test that settings correctly parse environment variables."""
    assert test_config.openrouter_api_key.get_secret_value().startswith("sk-or-v1-testkey")
    assert test_config.pinecone_api_key.get_secret_value().startswith("test-key-")
    assert test_config.text_fast_model == "test-fast"
    assert test_config.text_reasoning_model == "test-reason"
    assert test_config.multimodal_model == "test-vision"


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test default fallbacks when environment variables are missing."""
    # Temporarily set dummy keys so validation passes during initialization
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    monkeypatch.setenv("PINECONE_API_KEY", "dummy")
    settings = AppSettings()
    assert settings.text_fast_model == "google/gemini-2.5-flash"
    assert settings.text_reasoning_model == "deepseek/deepseek-reasoner"
    assert settings.multimodal_model == "google/gemini-2.5-pro"


def test_validate_keys_fails_on_missing_openrouter_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("PINECONE_API_KEY", "dummy_key")
    with pytest.raises(
        ValueError, match="OPENROUTER_API_KEY environment variable is not set or is empty."
    ):
        AppSettings()


def test_validate_keys_fails_on_missing_pinecone_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINECONE_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy_key")
    with pytest.raises(
        ValueError, match="PINECONE_API_KEY environment variable is not set or is empty."
    ):
        AppSettings()


def test_validate_keys_succeeds_when_both_keys_are_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy_router_key")
    monkeypatch.setenv("PINECONE_API_KEY", "dummy_pinecone_key")
    settings = AppSettings()
    # Should not raise any exception
    settings.validate_keys()
