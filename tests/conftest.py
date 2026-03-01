import uuid

import pytest

from src.core.config import AppSettings


class TestConfigFactory:
    """A factory class that generates AppSettings instances for tests to prevent hardcoding configuration defaults manually."""

    @staticmethod
    def create(tmp_path_str: str) -> AppSettings:
        from pathlib import Path
        return AppSettings(
            OPENROUTER_API_KEY=uuid.uuid4().hex,
            VECTOR_DB_URL="http://test-url.local",
            ALLOWED_DOCUMENT_DIR=Path(tmp_path_str),
            VDB_BATCH_SIZE=100,
            RETRY_MAX_ATTEMPTS=3,
            RETRY_DELAY_SECONDS=0,
            CIRCUIT_BREAKER_FAILURE_THRESHOLD=5,
            CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS=30,
            MAX_KEEPALIVE_CONNECTIONS=5,
            MAX_CONNECTIONS=10,
            ENVIRONMENT="test",
        )


@pytest.fixture
def app_settings(tmp_path: pytest.TempPathFactory) -> AppSettings:
    """Provides a centralized, isolated configuration fixture for tests."""
    return TestConfigFactory.create(str(tmp_path))
