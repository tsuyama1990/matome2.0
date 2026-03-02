from typing import Any, Protocol

from src.core.utils import with_retries
from src.domain.exceptions import ConfigurationError
from src.domain.models.document import DocumentChunk
from src.domain.ports.vector_store import IVectorStore


class PineconeIndexProtocol(Protocol):
    def upsert(self, vectors: list[dict[str, Any]]) -> None: ...
    def query(
        self,
        vector: list[float],
        top_k: int,
        filter_dict: dict[str, str] | None,
        include_metadata: bool,
    ) -> dict[str, Any]: ...
    def describe_index_stats(self) -> dict[str, Any]: ...


class PineconeIndexAdapter(PineconeIndexProtocol):
    """Adapter to map Pinecone SDK methods to the internal protocol."""

    def __init__(self, index: Any) -> None:
        self._index = index

    def upsert(self, vectors: list[dict[str, Any]]) -> None:
        self._index.upsert(vectors=vectors)

    def query(
        self,
        vector: list[float],
        top_k: int,
        filter_dict: dict[str, str] | None,
        include_metadata: bool,
    ) -> dict[str, Any]:
        res = self._index.query(
            vector=vector, top_k=top_k, filter=filter_dict, include_metadata=include_metadata
        )
        return dict(res) if isinstance(res, dict) else getattr(res, "to_dict", lambda: {})()

    def describe_index_stats(self) -> dict[str, Any]:
        res = self._index.describe_index_stats()
        return dict(res) if isinstance(res, dict) else getattr(res, "to_dict", lambda: {})()


class PineconeIndexFactory:
    """Factory to create and configure PineconeIndexProtocol instances."""

    @staticmethod
    def create_index(api_key: str, index_name: str) -> PineconeIndexProtocol:
        """Initializes and returns a configured Pinecone index."""
        from pinecone import Pinecone

        pc = Pinecone(api_key=api_key)
        return PineconeIndexAdapter(pc.Index(index_name))


class VectorStoreFactory:
    """Factory to create and configure IVectorStore instances."""

    @staticmethod
    def create_pinecone_client(index: PineconeIndexProtocol) -> "PineconeClient":
        """Initializes and returns a PineconeClient."""
        return PineconeClient(index=index)


class PineconeClient(IVectorStore):
    """Concrete implementation for Pinecone Vector Database."""

    _index: PineconeIndexProtocol

    def __init__(self, index: PineconeIndexProtocol) -> None:
        if index is None:
            msg = "Pinecone client must be initialized with a valid index"
            raise ConfigurationError(msg)
        self._index = index

    async def check_health(self, timeout: float = 5.0) -> bool:
        """Verifies if the vector store is reachable and configured."""
        try:
            self._index.describe_index_stats()
        except Exception:
            return False
        return True

    @with_retries(max_retries=3, base_delay=1.0)
    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Insert or update chunks into the vector store."""

        if len(chunks) > 10000:
            msg = "Batch size exceeds maximum allowed (10,000)"
            raise ValueError(msg)

        vectors = []
        for chunk in chunks:
            if not chunk.embedding:
                msg = f"Chunk {chunk.chunk_id} has no embedding"
                raise ValueError(msg)

            meta = {
                "document_id": str(chunk.document_id),
                "text": chunk.text,
            }
            meta.update(chunk.metadata)

            vectors.append(
                {
                    "id": str(chunk.chunk_id),
                    "values": chunk.embedding,
                    "metadata": meta,
                }
            )

        try:
            # Implement batching for large datasets
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                self._index.upsert(vectors=batch)
        except Exception as e:
            msg = f"Pinecone upsert failed: {e}"
            raise ConnectionError(msg) from e

    @with_retries(max_retries=3, base_delay=1.0)
    async def search_similar(
        self, query_embedding: list[float], top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[DocumentChunk]:
        """Search for semantically similar chunks."""
        if not query_embedding or not all(isinstance(x, (int, float)) for x in query_embedding):
            msg = "query_embedding must be a non-empty list of numeric values"
            raise ValueError(msg)

        try:
            results = self._index.query(
                vector=query_embedding, top_k=top_k, filter_dict=filters, include_metadata=True
            )
        except Exception as e:
            msg = f"Pinecone query failed: {e}"
            raise ConnectionError(msg) from e
        else:
            out_chunks = []
            matches = getattr(results, "matches", None)
            if matches is None and isinstance(results, dict):
                matches = results.get("matches", [])
            elif matches is None:
                matches = []

            for match in matches:
                # Handle either dict or object response from Pinecone
                meta = getattr(match, "metadata", None)
                if meta is None and isinstance(match, dict):
                    meta = match.get("metadata", {})
                elif meta is None:
                    meta = {}

                import uuid

                match_id = getattr(match, "id", None)
                if match_id is None and isinstance(match, dict):
                    match_id = match.get("id")
                if match_id is None:
                    match_id = str(uuid.uuid4())

                match_values = getattr(match, "values", None)
                if match_values is None and isinstance(match, dict):
                    match_values = match.get("values")
                # Recover original chunk
                out_chunks.append(
                    DocumentChunk(
                        chunk_id=uuid.UUID(str(match_id)),
                        document_id=meta.pop("document_id", "00000000-0000-0000-0000-000000000000"),
                        text=meta.pop("text", ""),
                        metadata=meta,
                        embedding=match_values,
                    )
                )
            return out_chunks
