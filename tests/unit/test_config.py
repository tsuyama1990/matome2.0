from src.core.config import AppSettings


def test_settings_initialization(test_config: AppSettings) -> None:
    """Test that settings correctly parse environment variables."""
    assert test_config.openrouter_api_key.startswith("test-key-")
    assert test_config.pinecone_api_key.startswith("test-key-")
    assert test_config.text_fast_model == "test-fast"
    assert test_config.text_reasoning_model == "test-reason"
    assert test_config.multimodal_model == "test-vision"


def test_settings_defaults() -> None:
    """Test default fallbacks when environment variables are missing."""
    settings = AppSettings()
    assert settings.text_fast_model == "google/gemini-2.5-flash"
    assert settings.text_reasoning_model == "deepseek/deepseek-reasoner"
    assert settings.multimodal_model == "google/gemini-2.5-pro"
