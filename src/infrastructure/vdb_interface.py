from abc import ABC, abstractmethod

from src.domain_models.chunk import SemanticChunk


class IVectorStore(ABC):
    """
    Abstract interface for Vector Database operations.
    """

    @abstractmethod
    async def upsert_chunks(self, chunks: list[SemanticChunk]) -> bool:
        """
        Upserts a list of SemanticChunks into the vector store.
        """

    @abstractmethod
    async def search(self, query_vector: list[float], limit: int) -> list[SemanticChunk]:
        """
        Searches the vector store using a query vector.
        """
