from unittest.mock import AsyncMock

import pytest

from src.core.config import AppSettings
from src.core.exceptions import MatomeAppError
from src.infrastructure.llm_interface import ILLMProvider
from src.infrastructure.vdb_interface import IVectorStore
from src.services.base_service import BaseService


def get_mock_llm_provider() -> AsyncMock:
    mock = AsyncMock(spec=ILLMProvider)
    mock.generate_completion.return_value = "mock completion"
    return mock


def get_mock_vector_store() -> AsyncMock:
    mock = AsyncMock(spec=IVectorStore)
    mock.upsert_chunks.return_value = True
    mock.upsert_chunks_batch.return_value = True
    mock.search.return_value = []
    mock.search_batch.return_value = []
    mock.stream_chunks_to_store.return_value = None
    return mock


class ConcreteService(BaseService):
    async def execute(self) -> None:
        pass


@pytest.fixture
def test_config(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory) -> AppSettings:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("VECTOR_DB_URL", "http://test")
    monkeypatch.setenv("VDB_BATCH_SIZE", "100")
    monkeypatch.setenv("RETRY_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("ALLOWED_DOCUMENT_DIR", str(tmp_path))
    return AppSettings(_env_file=None)  # type: ignore[call-arg]


def test_base_service_init(test_config: AppSettings) -> None:
    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    service = ConcreteService(llm_provider=llm, vector_store=vdb, config=test_config)
    assert service.llm_provider is llm
    assert service.vector_store is vdb


@pytest.mark.asyncio
async def test_execute_with_retry_success(test_config: AppSettings) -> None:
    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    service = ConcreteService(llm_provider=llm, vector_store=vdb, config=test_config)

    async def mock_operation() -> str:
        return "success"

    result: str = await service.execute_with_retry(mock_operation)
    assert result == "success"


@pytest.mark.asyncio
async def test_execute_with_retry_matome_app_exception(
    monkeypatch: pytest.MonkeyPatch, test_config: AppSettings
) -> None:
    import asyncio

    original_sleep = asyncio.sleep

    async def mock_sleep(x: float) -> None:
        await original_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)
    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    test_config.RETRY_MAX_ATTEMPTS = 2
    service = ConcreteService(llm_provider=llm, vector_store=vdb, config=test_config)

    attempts = 0

    async def mock_operation() -> str:
        nonlocal attempts
        attempts += 1
        msg = "Test error"
        raise MatomeAppError(msg)

    with pytest.raises(MatomeAppError, match="Test error"):
        await service.execute_with_retry(mock_operation)

    assert attempts == 2


@pytest.mark.asyncio
async def test_execute_with_retry_generic_exception(test_config: AppSettings) -> None:
    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    service = ConcreteService(llm_provider=llm, vector_store=vdb, config=test_config)

    async def mock_operation() -> str:
        msg = "Generic error"
        raise ValueError(msg)

    with pytest.raises(MatomeAppError, match="Operation failed: Generic error"):
        await service.execute_with_retry(mock_operation)


@pytest.mark.asyncio
async def test_execute_with_retry_circuit_breaker(
    monkeypatch: pytest.MonkeyPatch, test_config: AppSettings
) -> None:
    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    test_config.RETRY_MAX_ATTEMPTS = 1  # 1 try per call
    service = ConcreteService(llm_provider=llm, vector_store=vdb, config=test_config)

    async def fail_op() -> str:
        msg = "fail"
        raise MatomeAppError(msg)

    # Trip breaker
    for _ in range(5):
        with pytest.raises(MatomeAppError):
            await service.execute_with_retry(fail_op)

    # Breaker should now be open
    from src.services.base_service import CircuitBreakerOpenError

    with pytest.raises(CircuitBreakerOpenError, match="Circuit is currently open"):
        await service.execute_with_retry(fail_op)


@pytest.mark.asyncio
async def test_execute_with_retry_recovers(
    monkeypatch: pytest.MonkeyPatch, test_config: AppSettings
) -> None:
    import asyncio

    async def mock_sleep(x: float) -> None:
        pass

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    test_config.RETRY_MAX_ATTEMPTS = 3
    service = ConcreteService(llm_provider=llm, vector_store=vdb, config=test_config)

    attempts = 0

    async def mock_operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            msg = "Temporary failure"
            raise MatomeAppError(msg)
        return "success"

    result = await service.execute_with_retry(mock_operation)
    assert result == "success"
    assert attempts == 3
