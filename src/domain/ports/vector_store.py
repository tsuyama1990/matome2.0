from abc import ABC, abstractmethod

from src.domain.models.document import DocumentChunk


class IVectorStore(ABC):
    """Abstract interface for a Vector Database.

    Implementations are strictly expected to provide error handling
    and transient retry logic against upstream service availability drops.
    """

    @abstractmethod
    async def check_health(self, timeout: float | None = None) -> bool:
        """Verifies if the vector store is reachable and configured.

        Implementations must enforce strict timeout boundaries (e.g. 5 seconds)
        to prevent application hangs during degraded downstream service availability.
        This method should internally catch any ConnectionError, TimeoutError,
        or provider-specific exceptions and return False instead of raising.

        Returns:
            bool: True if the connection is healthy, otherwise False.
        """

    @abstractmethod
    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Insert or update chunks into the vector store.

        Args:
            chunks (list[DocumentChunk]): List of chunk objects to be stored/indexed.

        Raises:
            ConnectionError: If the connection to the vector DB fails.
            ValueError: If the chunk data is invalid or embedding dimensions do not match.
        """

    @abstractmethod
    async def search_similar(
        self, query_embedding: list[float], top_k: int, filters: dict[str, str] | None = None
    ) -> list[DocumentChunk]:
        """Search for semantically similar chunks."""

    @abstractmethod
    async def delete_chunks(self, chunk_ids: list[str]) -> None:
        """Deletes chunks from the vector store in a batch."""
