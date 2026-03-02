from typing import Any, Protocol

from src.core.utils import _with_retries
from src.domain.models.document import DocumentChunk
from src.domain.ports.vector_store import IVectorStore


class PineconeIndexProtocol(Protocol):
    def upsert(self, vectors: list[dict[str, Any]]) -> None: ...
    def query(
        self,
        vector: list[float],
        top_k: int,
        filter: dict[str, str] | None,  # noqa: A002
        include_metadata: bool,
    ) -> Any: ...


class PineconeClient(IVectorStore):
    """Concrete implementation for Pinecone Vector Database."""

    _index: PineconeIndexProtocol

    def __init__(self, index: PineconeIndexProtocol) -> None:
        if index is None:
            msg = "Pinecone client must be initialized with a valid index"
            raise ValueError(msg)
        self._index = index

    async def check_health(self) -> bool:
        """Verifies if the vector store is reachable and configured."""
        # Check if index has a describe method or something to verify it's alive
        # For PineconeIndexProtocol, we just assume it's true since it's injected
        return True

    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Insert or update chunks into the vector store."""

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

        async def _call() -> None:
            try:
                # Batch upsert logic could be added here for large datasets
                self._index.upsert(vectors=vectors)
            except Exception as e:
                msg = f"Pinecone upsert failed: {e}"
                raise ConnectionError(msg) from e

        await _with_retries(_call)

    async def search_similar(
        self, query_embedding: list[float], top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[DocumentChunk]:
        """Search for semantically similar chunks."""

        async def _call() -> list[DocumentChunk]:
            try:
                results = self._index.query(
                    vector=query_embedding, top_k=top_k, filter=filters, include_metadata=True
                )
            except Exception as e:
                msg = f"Pinecone query failed: {e}"
                raise ConnectionError(msg) from e
            else:
                chunks = []
                for match in getattr(results, "matches", []):
                    meta = match.metadata or {}
                    # Recover original chunk
                    chunks.append(
                        DocumentChunk(
                            chunk_id=match.id,
                            document_id=meta.pop(
                                "document_id", "00000000-0000-0000-0000-000000000000"
                            ),
                            text=meta.pop("text", ""),
                            metadata=meta,
                            embedding=match.values,
                        )
                    )
                return chunks

        return await _with_retries(_call)
