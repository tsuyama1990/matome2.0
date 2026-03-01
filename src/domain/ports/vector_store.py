from abc import ABC, abstractmethod

from src.domain.models.document import DocumentChunk


class IVectorStore(ABC):
    """Abstract interface for a Vector Database."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initializes or configures the vector store. Must be called before use."""

    @abstractmethod
    async def check_health(self) -> bool:
        """Verifies if the vector store is reachable and configured.

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
        self, query_embedding: list[float], top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[DocumentChunk]:
        """Search for semantically similar chunks.

        This method must be highly performant, utilizing approximate nearest neighbor
        (ANN / HNSW) algorithms capable of millisecond latency.

        Args:
            query_embedding (list[float]): The embedded vector query.
            top_k (int): Number of most similar results to return.
            filters (dict | None): Metadata filters to apply before or during the search.

        Returns:
            list[DocumentChunk]: A list of chunks matching the query.

        Raises:
            ConnectionError: If the search request times out or DB is unreachable.
            ValueError: If the query embedding has a dimension mismatch.
        """
