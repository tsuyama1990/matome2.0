from abc import ABC, abstractmethod

from src.domain.models.document import DocumentChunk


class IVectorStore(ABC):
    """Abstract interface for a Vector Database."""

    @abstractmethod
    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Insert or update chunks into the vector store."""

    @abstractmethod
    async def search_similar(
        self, query_embedding: list[float], top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[DocumentChunk]:
        """Search for semantically similar chunks."""
