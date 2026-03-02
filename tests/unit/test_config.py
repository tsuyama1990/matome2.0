import pytest

from src.core.config import AppSettings


def test_settings_initialization(test_config: AppSettings) -> None:
    """Test that settings correctly parse environment variables."""
    assert test_config.llm.api_key.get_secret_value().startswith("sk-or-v1-testkey")
    assert test_config.vector_store.api_key.get_secret_value().startswith("test-key-")
    assert test_config.llm.text_fast_model == "test-fast"
    assert test_config.llm.text_reasoning_model == "test-reason"
    assert test_config.llm.multimodal_model == "test-vision"


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test default fallbacks when environment variables are missing."""
    # Temporarily set dummy keys so validation passes during initialization
    monkeypatch.setenv("LLM__API_KEY", "dummy")
    monkeypatch.setenv("VECTOR_STORE__API_KEY", "dummy")
    settings = AppSettings()
    assert settings.llm.text_fast_model == "google/gemini-2.5-flash"
    assert settings.llm.text_reasoning_model == "deepseek/deepseek-reasoner"
    assert settings.llm.multimodal_model == "google/gemini-2.5-pro"


def test_validate_keys_fails_on_missing_openrouter_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM__API_KEY", "")
    monkeypatch.setenv("VECTOR_STORE__API_KEY", "dummy_key")
    with pytest.raises(
        ValueError, match="OPENROUTER_API_KEY environment variable is not set or is empty."
    ):
        AppSettings()


def test_validate_keys_fails_on_missing_pinecone_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECTOR_STORE__API_KEY", "")
    monkeypatch.setenv("LLM__API_KEY", "dummy_key")
    with pytest.raises(
        ValueError, match="PINECONE_API_KEY environment variable is not set or is empty."
    ):
        AppSettings()


def test_validate_keys_succeeds_when_both_keys_are_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM__API_KEY", "dummy_router_key")
    monkeypatch.setenv("VECTOR_STORE__API_KEY", "dummy_pinecone_key")
    settings = AppSettings()
    # Should not raise any exception
    from src.core.config import ConfigValidator

    ConfigValidator.validate_keys(settings)


from pydantic import SecretStr


def test_app_settings_post_init_validates() -> None:
    # Testing that model_post_init is implicitly called and raises
    # if we bypass the environment variables
    from src.core.config import LLMSettings, VectorStoreSettings

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY environment variable is not set"):
        # We explicitly supply empty strings to bypass defaults and force validation
        AppSettings(
            llm=LLMSettings(api_key=SecretStr("")),
            vector_store=VectorStoreSettings(api_key=SecretStr("mock")),
        )

    with pytest.raises(ValueError, match="PINECONE_API_KEY environment variable is not set"):
        AppSettings(
            llm=LLMSettings(api_key=SecretStr("mock")),
            vector_store=VectorStoreSettings(api_key=SecretStr("")),
        )


def test_validate_keys_fails_on_missing_production_keys() -> None:
    from src.core.config import LLMSettings, VectorStoreSettings

    with pytest.raises(
        ValueError,
        match="Production environment requires both OPENROUTER_API_KEY and PINECONE_API_KEY.",
    ):
        AppSettings(
            environment="prod",
            llm=LLMSettings(api_key=SecretStr("")),
            vector_store=VectorStoreSettings(api_key=SecretStr("")),
        )

    with pytest.raises(
        ValueError,
        match="Production environment requires both OPENROUTER_API_KEY and PINECONE_API_KEY.",
    ):
        AppSettings(
            environment="prod",
            llm=LLMSettings(api_key=SecretStr("key")),
            vector_store=VectorStoreSettings(api_key=SecretStr("")),
        )


from pathlib import Path


def test_load_defaults_invalid_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.config

    # create invalid config
    cfg = tmp_path / "config.json"
    cfg.write_text("{invalid")

    with monkeypatch.context() as m:
        m.setattr("src.core.config.Path.exists", lambda self: True)
        m.setattr("src.core.config.Path.read_text", lambda self: "{invalid")

        result = src.core.config._load_defaults()
        assert result == {}


def test_load_defaults_file_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.config

    with monkeypatch.context() as m:
        m.setattr("src.core.config.Path.exists", lambda self: False)

        result = src.core.config._load_defaults()
        assert result == {}
