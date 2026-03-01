from collections.abc import AsyncGenerator

from src.domain_models.chunk import SemanticChunk
from src.infrastructure.llm_interface import ILLMProvider
from src.infrastructure.vdb_interface import IVectorStore


class MockLLMProvider(ILLMProvider):
    async def generate_completion(self, prompt: str) -> str:
        return "mock completion"


class MockVectorStore(IVectorStore):
    async def upsert_chunks(self, chunks: list[SemanticChunk]) -> bool:
        return True

    async def search(self, query_vector: list[float], limit: int) -> list[SemanticChunk]:
        return []


async def get_llm_provider() -> AsyncGenerator[ILLMProvider, None]:
    """Yields a MockLLMProvider instance for dependency injection."""
    yield MockLLMProvider()


async def get_vector_store() -> AsyncGenerator[IVectorStore, None]:
    """Yields a MockVectorStore instance for dependency injection."""
    yield MockVectorStore()
