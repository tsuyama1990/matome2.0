from uuid import uuid4

import pytest

from src.core.config import AppSettings


class TestConfigFactory:
    """Factory to generate dynamically hydrated AppSettings for tests."""

    @staticmethod
    def create(monkeypatch: pytest.MonkeyPatch) -> AppSettings:
        """Returns a new AppSettings instance with mocked configuration."""
        monkeypatch.setenv("LLM__API_KEY", f"sk-or-v1-testkey{uuid4().hex}")
        monkeypatch.setenv("VECTOR_STORE__API_KEY", f"test-key-{uuid4()}")
        monkeypatch.setenv("LLM__TEXT_FAST_MODEL", "test-fast")
        monkeypatch.setenv("LLM__TEXT_REASONING_MODEL", "test-reason")
        monkeypatch.setenv("LLM__MULTIMODAL_MODEL", "test-vision")
        monkeypatch.setenv("LLM__BASE_URL", "http://test-api")
        from src.core.config import ConfigFactory
        return ConfigFactory.create_settings()


@pytest.fixture
def test_config(monkeypatch: pytest.MonkeyPatch) -> AppSettings:
    """Provides a dynamically hydrated AppSettings to avoid side-effects.

    This fixture ensures that tests interacting with the configuration use mocked values
    rather than attempting to read from the local environment. It guarantees tests remain
    isolated and predictable, preventing side effects from leaking across test executions.
    """
    return TestConfigFactory.create(monkeypatch)
