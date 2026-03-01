from abc import ABC, abstractmethod

from src.domain_models.chunk import SemanticChunk


class IVectorStore(ABC):
    @abstractmethod
    async def upsert_chunks(self, chunks: list[SemanticChunk]) -> bool:
        pass

    @abstractmethod
    async def upsert_chunks_batch(self, chunks: list[SemanticChunk], batch_size: int = 1000) -> bool:
        pass

    @abstractmethod
    async def search(self, query_vector: list[float], limit: int) -> list[SemanticChunk]:
        pass

    @abstractmethod
    async def search_batch(self, query_vectors: list[list[float]], limit: int) -> list[list[SemanticChunk]]:
        pass
