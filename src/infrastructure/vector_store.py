import asyncio
import logging
import typing
from dataclasses import dataclass
from typing import Any, Protocol

from src.core.constants import (
    ERR_BATCH_SIZE_EXCEEDED,
    ERR_EMPTY_EMBEDDING,
    ERR_INVALID_OR_MISSING_EMBEDDING,
    ERR_INVALID_PINECONE_API_KEY_FORMAT,
    ERR_PINECONE_ADAPTER_QUERY_01,
    ERR_PINECONE_ADAPTER_STATS_01,
    ERR_PINECONE_ADAPTER_UPSERT_01,
    ERR_PINECONE_SEARCH_01,
    ERR_PINECONE_UPSERT_01,
)
from src.core.utils import _with_retries, validate_embedding
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
    ) -> Any: ...
    def describe_index_stats(self) -> Any: ...


class PineconeIndexAdapter(PineconeIndexProtocol):
    """Adapter to map Pinecone SDK methods to the internal protocol."""

    def __init__(self, index: typing.Any) -> None:  # Using typing.Any because the official Pinecone SDK is untyped and dynamic
        self._index = index

    def upsert(self, vectors: list[dict[str, Any]]) -> None:
        try:
            self._index.upsert(vectors=vectors)
        except Exception as e:
            logging.exception(ERR_PINECONE_ADAPTER_UPSERT_01)
            raise ConnectionError(ERR_PINECONE_ADAPTER_UPSERT_01) from e

    def query(
        self,
        vector: list[float],
        top_k: int,
        filter_dict: dict[str, str] | None,
        include_metadata: bool,
    ) -> Any:
        try:
            res = self._index.query(
                vector=vector, top_k=top_k, filter=filter_dict, include_metadata=include_metadata
            )
            return dict(res) if isinstance(res, dict) else getattr(res, "to_dict", dict)()
        except Exception as e:
            logging.exception(ERR_PINECONE_ADAPTER_QUERY_01)
            raise ConnectionError(ERR_PINECONE_ADAPTER_QUERY_01) from e

    def describe_index_stats(self) -> Any:
        try:
            res = self._index.describe_index_stats()
            return dict(res) if isinstance(res, dict) else getattr(res, "to_dict", dict)()
        except Exception as e:
            logging.exception(ERR_PINECONE_ADAPTER_STATS_01)
            raise ConnectionError(ERR_PINECONE_ADAPTER_STATS_01) from e


class PineconeIndexFactory:
    """Factory to create and configure PineconeIndexProtocol instances."""

    @staticmethod
    def create_index(api_key: str, index_name: str) -> PineconeIndexProtocol:
        """Initializes and returns a configured Pinecone index."""
        import re
        if not api_key or not isinstance(api_key, str) or len(api_key) < 30 or not re.match(r"^[a-zA-Z0-9\-]+$", api_key):
            raise ValueError(ERR_INVALID_PINECONE_API_KEY_FORMAT)

        from pinecone import Pinecone
        pc = Pinecone(api_key=api_key)
        return PineconeIndexAdapter(pc.Index(index_name))


@dataclass
class PineconeConfig:
    max_retries: int
    base_delay: float
    batch_size: int
    max_batch_size: int


class VectorStoreFactory:
    """Factory to create and configure IVectorStore instances."""

    @staticmethod
    def create_pinecone_client(
        index: PineconeIndexProtocol, config: PineconeConfig
    ) -> "PineconeClient":
        """Initializes and returns a PineconeClient."""
        return PineconeClient(index=index, config=config)


class PineconeClient(IVectorStore):
    """Concrete implementation for Pinecone Vector Database."""

    _index: PineconeIndexProtocol
    _config: PineconeConfig

    def __init__(self, index: PineconeIndexProtocol, config: PineconeConfig) -> None:
        if index is None:
            msg = "Pinecone client must be initialized with a valid index"
            raise ConfigurationError(msg)
        self._index = index
        self._config = config

    async def check_health(self, timeout: float | None = None) -> bool:
        """Verifies if the vector store is reachable and configured."""
        try:
            if timeout:
                await asyncio.wait_for(
                    asyncio.to_thread(self._index.describe_index_stats), timeout=timeout
                )
            else:
                await asyncio.to_thread(self._index.describe_index_stats)
        except Exception:
            return False
        return True

    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Insert or update chunks into the vector store."""

        async def _func() -> None:
            await self._upsert_chunks(chunks)

        await _with_retries(_func, self._config.max_retries, self._config.base_delay)

    async def _upsert_chunks(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            return

        if len(chunks) > self._config.max_batch_size:
            raise ValueError(ERR_BATCH_SIZE_EXCEEDED.format(max_batch_size=self._config.max_batch_size))

        vectors = []
        for chunk in chunks:
            if chunk.embedding is None or not isinstance(chunk.embedding, list):
                raise ValueError(ERR_INVALID_OR_MISSING_EMBEDDING.format(chunk_id=chunk.chunk_id))

            if len(chunk.embedding) == 0:
                raise ValueError(ERR_EMPTY_EMBEDDING.format(chunk_id=chunk.chunk_id))

            # To avoid exposing raw text in vector DB metadata (Data Minimization)
            meta = {
                "document_id": str(chunk.document_id),
            }

            if isinstance(chunk.metadata, dict):
                for k, v in chunk.metadata.items():
                    # explicitly exclude text if someone shoved it in metadata
                    if k == "text":
                        continue
                    if isinstance(v, (str, int, float, bool)):
                        meta[k] = str(v)

            vectors.append(
                {
                    "id": str(chunk.chunk_id),
                    "values": chunk.embedding,
                    "metadata": meta,
                }
            )

        try:
            # Implement batching for large datasets
            batch_size = self._config.batch_size
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                self._index.upsert(vectors=batch)
        except Exception as e:
            logging.exception(ERR_PINECONE_UPSERT_01)
            raise ConnectionError(ERR_PINECONE_UPSERT_01) from e

    async def search_similar(
        self, query_embedding: list[float], top_k: int, filters: dict[str, str] | None = None
    ) -> list[DocumentChunk]:
        """Search for semantically similar chunks."""

        async def _func() -> list[DocumentChunk]:
            return await self._search_similar(query_embedding, top_k, filters)

        return await _with_retries(_func, self._config.max_retries, self._config.base_delay)

    def _parse_match(self, match: typing.Any) -> DocumentChunk:
        import uuid
        meta = getattr(match, "metadata", None)
        if meta is None and isinstance(match, dict):
            meta = match.get("metadata", {})
        if meta is None:
            meta = {}

        match_id = getattr(match, "id", None)
        if match_id is None and isinstance(match, dict):
            match_id = match.get("id")
        if match_id is None or not isinstance(match_id, str):
            match_id = str(uuid.uuid4())
        else:
            try:
                uuid.UUID(match_id)
            except ValueError:
                match_id = str(uuid.uuid4())

        match_values = getattr(match, "values", None)
        if match_values is None and isinstance(match, dict):
            match_values = match.get("values")
        if callable(match_values):
            match_values = None
        # Recover original chunk
        doc_id = meta.pop("document_id", "00000000-0000-0000-0000-000000000000")
        if not doc_id:
            doc_id = "00000000-0000-0000-0000-000000000000"
        else:
            try:
                uuid.UUID(str(doc_id))
            except ValueError:
                doc_id = "00000000-0000-0000-0000-000000000000"

        return DocumentChunk(
            chunk_id=uuid.UUID(str(match_id)),
            document_id=uuid.UUID(str(doc_id)),
            text="",  # Text is omitted from metadata per security minimization
            metadata=meta,
            embedding=match_values,
        )

    async def _search_similar(
        self, query_embedding: list[float], top_k: int, filters: dict[str, str] | None = None
    ) -> list[DocumentChunk]:
        validate_embedding(query_embedding)

        # Hard limit to prevent abuse / memory exhaustion
        limit = min(top_k, 10000)

        try:
            results = self._index.query(
                vector=query_embedding, top_k=limit, filter_dict=filters, include_metadata=True
            )
        except Exception as e:
            logging.exception(ERR_PINECONE_SEARCH_01)
            raise ConnectionError(ERR_PINECONE_SEARCH_01) from e
        else:
            out_chunks = []
            matches = getattr(results, "matches", None)
            if matches is None and isinstance(results, dict):
                matches = results.get("matches", [])
            elif matches is None:
                matches = []

            for match in matches:
                out_chunks.append(self._parse_match(match))
            return out_chunks
