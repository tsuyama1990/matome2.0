import os
from uuid import uuid4

import pytest

from src.core.config import AppSettings


@pytest.fixture
def test_config() -> AppSettings:
    """Provides a dynamically hydrated AppSettings to avoid side-effects.

    This fixture ensures that tests interacting with the configuration use mocked values
    rather than attempting to read from the local environment. It guarantees tests remain
    isolated and predictable, preventing side effects from leaking across test executions.
    """
    os.environ["OPENROUTER_API_KEY"] = f"test-key-{uuid4()}"
    os.environ["PINECONE_API_KEY"] = f"test-key-{uuid4()}"
    os.environ["TEXT_FAST_MODEL"] = "test-fast"
    os.environ["TEXT_REASONING_MODEL"] = "test-reason"
    os.environ["MULTIMODAL_MODEL"] = "test-vision"

    settings = AppSettings()

    del os.environ["OPENROUTER_API_KEY"]
    del os.environ["PINECONE_API_KEY"]
    del os.environ["TEXT_FAST_MODEL"]
    del os.environ["TEXT_REASONING_MODEL"]
    del os.environ["MULTIMODAL_MODEL"]

    return settings
