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


class ConcreteService(BaseService[str]):
    async def execute(self) -> str:
        return "success"


def test_base_service_init(app_settings: AppSettings) -> None:
    from src.api.dependencies import Container

    container = Container()
    container.config.override(app_settings)

    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    container.llm_provider.override(llm)
    container.vector_store.override(vdb)

    service = ConcreteService(
        llm_provider=container.llm_provider(),
        vector_store=container.vector_store(),
        config=container.config(),
    )
    assert service.llm_provider is llm
    assert service.vector_store is vdb


@pytest.mark.asyncio
async def test_execute_with_retry_success(app_settings: AppSettings) -> None:
    from src.api.dependencies import Container

    container = Container()
    container.config.override(app_settings)

    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    container.llm_provider.override(llm)
    container.vector_store.override(vdb)

    service = ConcreteService(
        llm_provider=container.llm_provider(),
        vector_store=container.vector_store(),
        config=container.config(),
    )

    async def mock_operation() -> str:
        return "success"

    result: str = await service.execute_with_retry(mock_operation)
    assert result == "success"


@pytest.mark.asyncio
async def test_execute_with_retry_matome_app_exception(
    monkeypatch: pytest.MonkeyPatch, app_settings: AppSettings
) -> None:
    import asyncio

    original_sleep = asyncio.sleep

    async def mock_sleep(x: float) -> None:
        await original_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)
    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    app_settings.RETRY_MAX_ATTEMPTS = 2
    service = ConcreteService(llm_provider=llm, vector_store=vdb, config=app_settings)

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
async def test_execute_with_retry_generic_exception(
    app_settings: AppSettings, caplog: pytest.LogCaptureFixture
) -> None:
    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    service = ConcreteService(llm_provider=llm, vector_store=vdb, config=app_settings)

    async def mock_operation() -> str:
        msg = "Generic error"
        raise ValueError(msg)

    with pytest.raises(MatomeAppError, match="Operation failed: Generic error"):
        await service.execute_with_retry(mock_operation)

    assert "Operation failed: Generic error" in caplog.text


@pytest.mark.asyncio
async def test_execute_with_retry_circuit_breaker(
    monkeypatch: pytest.MonkeyPatch, app_settings: AppSettings
) -> None:
    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    app_settings.RETRY_MAX_ATTEMPTS = 1  # 1 try per call
    service = ConcreteService(llm_provider=llm, vector_store=vdb, config=app_settings)

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
    monkeypatch: pytest.MonkeyPatch, app_settings: AppSettings
) -> None:
    import asyncio

    async def mock_sleep(x: float) -> None:
        pass

    monkeypatch.setattr(asyncio, "sleep", mock_sleep)

    llm = get_mock_llm_provider()
    vdb = get_mock_vector_store()
    app_settings.RETRY_MAX_ATTEMPTS = 3
    service = ConcreteService(llm_provider=llm, vector_store=vdb, config=app_settings)

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
