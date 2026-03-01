from src.domain_models.chunk import SemanticChunk
from src.infrastructure.vdb_interface import IVectorStore


class PineconeVectorStore(IVectorStore):
    async def upsert_chunks(self, chunks: list[SemanticChunk]) -> bool:
        return True

    async def upsert_chunks_batch(
        self, chunks: list[SemanticChunk], batch_size: int = 1000
    ) -> bool:
        """Upsert chunks in configured batch sizes to prevent payload too large errors."""
        import logging

        logger = logging.getLogger(__name__)

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            try:
                await self.upsert_chunks(batch)
            except Exception as e:
                logger.exception("Failed to upsert batch starting at index %d: %s", i, e)
                return False
        return True

    async def stream_chunks_to_store(self, document_id: str, document_path: str) -> None:
        pass

    async def search(
        self, query_vector: list[float], limit: int, offset: int = 0
    ) -> list[SemanticChunk]:
        return []

    async def search_batch(
        self, query_vectors: list[list[float]], limit: int, offset: int = 0
    ) -> list[list[SemanticChunk]]:
        return []
