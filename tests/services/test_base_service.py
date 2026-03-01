import pytest

from src.core.exceptions import MatomeAppError
from src.domain_models.chunk import SemanticChunk
from src.infrastructure.llm_interface import ILLMProvider
from src.infrastructure.vdb_interface import IVectorStore
from src.services.base_service import BaseService


class MockLLMProvider(ILLMProvider):
    async def generate_completion(self, prompt: str) -> str:
        return "mock completion"

class MockVectorStore(IVectorStore):
    async def upsert_chunks(self, chunks: list[SemanticChunk]) -> bool:
        return True

    async def upsert_chunks_batch(self, chunks: list[SemanticChunk], batch_size: int = 1000) -> bool:
        return True

    async def search(self, query_vector: list[float], limit: int) -> list[SemanticChunk]:
        return []

    async def search_batch(self, query_vectors: list[list[float]], limit: int) -> list[list[SemanticChunk]]:
        return []

class ConcreteService(BaseService):
    async def execute(self) -> None:
        pass

def test_base_service_init() -> None:
    llm = MockLLMProvider()
    vdb = MockVectorStore()
    service = ConcreteService(llm_provider=llm, vector_store=vdb)
    assert service.llm_provider is llm
    assert service.vector_store is vdb

@pytest.mark.asyncio
async def test_execute_with_retry_success() -> None:
    llm = MockLLMProvider()
    vdb = MockVectorStore()
    service = ConcreteService(llm_provider=llm, vector_store=vdb)

    async def mock_operation() -> str:
        return "success"

    result: str = await service.execute_with_retry(mock_operation, max_retries=3)
    assert result == "success"

@pytest.mark.asyncio
async def test_execute_with_retry_matome_app_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio
    original_sleep = asyncio.sleep
    async def mock_sleep(x: float) -> None:
        await original_sleep(0)
    monkeypatch.setattr(asyncio, "sleep", mock_sleep)
    llm = MockLLMProvider()
    vdb = MockVectorStore()
    service = ConcreteService(llm_provider=llm, vector_store=vdb)

    attempts = 0

    async def mock_operation() -> str:
        nonlocal attempts
        attempts += 1
        msg = "Test error"
        raise MatomeAppError(msg)

    with pytest.raises(MatomeAppError, match="Test error"):
        await service.execute_with_retry(mock_operation, max_retries=2)

    assert attempts == 2

@pytest.mark.asyncio
async def test_execute_with_retry_generic_exception() -> None:
    llm = MockLLMProvider()
    vdb = MockVectorStore()
    service = ConcreteService(llm_provider=llm, vector_store=vdb)

    async def mock_operation() -> str:
        msg = "Generic error"
        raise ValueError(msg)

    with pytest.raises(MatomeAppError, match="Operation failed: Generic error"):
        await service.execute_with_retry(mock_operation, max_retries=3)
