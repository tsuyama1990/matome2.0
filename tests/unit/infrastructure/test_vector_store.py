import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.domain.exceptions import ConfigurationError
from src.domain.models.document import DocumentChunk
from src.infrastructure.vector_store import PineconeClient, PineconeConfig, PineconeIndexProtocol


@pytest.fixture
def mock_pinecone_index() -> MagicMock:
    return MagicMock()


@pytest.fixture
def vector_client(mock_pinecone_index: MagicMock) -> PineconeClient:
    return PineconeClient(
        index=mock_pinecone_index,
        config=PineconeConfig(max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000),
    )


@pytest.mark.asyncio
async def test_check_health(vector_client: PineconeClient) -> None:
    assert await vector_client.check_health() is True


@pytest.mark.asyncio
async def test_check_health_failure() -> None:
    with pytest.raises(
        ConfigurationError, match="Pinecone client must be initialized with a valid index"
    ):
        PineconeClient(
            index=None,  # type: ignore
            config=PineconeConfig(
                max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000
            ),
        )


@pytest.mark.asyncio
async def test_upsert_chunks_success(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    chunk = DocumentChunk(
        chunk_id=uuid4(), document_id=uuid4(), text="Test", embedding=[0.1, 0.2, 0.3]
    )

    await vector_client.upsert_chunks([chunk])
    mock_pinecone_index.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_chunks_missing_embedding(vector_client: PineconeClient) -> None:
    chunk = DocumentChunk(chunk_id=uuid4(), document_id=uuid4(), text="Test", embedding=None)

    with pytest.raises(ValueError, match="has no embedding"):
        await vector_client.upsert_chunks([chunk])


@pytest.mark.asyncio
async def test_search_similar_success(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    # Setup mock return
    mock_match = MagicMock()
    mock_match.id = str(uuid4())
    mock_match.values = [0.1, 0.2, 0.3]
    mock_match.metadata = {
        "document_id": str(uuid4()),
        "text": "Test result",
        "extra_meta": "value",
    }

    mock_response = MagicMock()
    mock_response.matches = [mock_match]
    mock_pinecone_index.query.return_value = mock_response

    results = await vector_client.search_similar(query_embedding=[0.1, 0.2, 0.3], top_k=5)

    assert len(results) == 1
    assert results[0].text == "Test result"
    assert results[0].metadata["extra_meta"] == "value"


@pytest.mark.asyncio
async def test_search_similar_connection_error(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    mock_pinecone_index.query.side_effect = Exception("Network down")

    with pytest.raises(ConnectionError, match="Pinecone query failed"):
        await vector_client.search_similar(query_embedding=[0.1, 0.2, 0.3], top_k=5)


@pytest.mark.asyncio
async def test_upsert_chunks_retry_success(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    chunk = DocumentChunk(
        chunk_id=uuid4(), document_id=uuid4(), text="Test", embedding=[0.1, 0.2, 0.3]
    )

    mock_pinecone_index.upsert.side_effect = [Exception("Network down"), None]

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        await vector_client.upsert_chunks([chunk])
    assert mock_pinecone_index.upsert.call_count == 2


@pytest.mark.asyncio
async def test_upsert_chunks_retry_failure(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    chunk = DocumentChunk(
        chunk_id=uuid4(), document_id=uuid4(), text="Test", embedding=[0.1, 0.2, 0.3]
    )

    mock_pinecone_index.upsert.side_effect = Exception("Network down")

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        with pytest.raises(ConnectionError, match="Pinecone upsert failed"):
            await vector_client.upsert_chunks([chunk])

    assert mock_pinecone_index.upsert.call_count == 3


@pytest.mark.asyncio
async def test_search_similar_retry_success(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    mock_match = MagicMock()
    mock_match.id = str(uuid4())
    mock_match.values = [0.1, 0.2, 0.3]
    mock_match.metadata = {
        "document_id": str(uuid4()),
        "text": "Test result",
        "extra_meta": "value",
    }

    mock_response = MagicMock()
    mock_response.matches = [mock_match]

    mock_pinecone_index.query.side_effect = [Exception("Network down"), mock_response]

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        results = await vector_client.search_similar(query_embedding=[0.1, 0.2, 0.3], top_k=5)

    assert len(results) == 1
    assert results[0].text == "Test result"
    assert mock_pinecone_index.query.call_count == 2


@pytest.mark.asyncio
async def test_search_similar_retry_failure(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    mock_pinecone_index.query.side_effect = Exception("Network down")

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        with pytest.raises(ConnectionError, match="Pinecone query failed"):
            await vector_client.search_similar(query_embedding=[0.1, 0.2, 0.3], top_k=5)

    assert mock_pinecone_index.query.call_count == 3


@pytest.mark.asyncio
async def test_check_health_exception() -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    mock_index.describe_index_stats.side_effect = Exception("failed")
    client = PineconeClient(
        index=mock_index,
        config=PineconeConfig(max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000),
    )

    assert await client.check_health() is False


@pytest.mark.asyncio
async def test_upsert_chunks_batching() -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=PineconeConfig(max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000),
    )

    chunks = []
    for _ in range(150):  # > 100 to trigger batching loop
        chunks.append(
            DocumentChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                text="Sample",
                embedding=[0.1, 0.2, 0.3],
            )
        )

    await client.upsert_chunks(chunks)
    assert mock_index.upsert.call_count == 2


@pytest.mark.asyncio
async def test_search_similar_invalid_query() -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=PineconeConfig(max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000),
    )

    with pytest.raises(
        ValueError, match="query_embedding must be a non-empty list of numeric values"
    ):
        await client.search_similar([], top_k=5)

    with pytest.raises(
        ValueError, match="query_embedding must be a non-empty list of numeric values"
    ):
        await client.search_similar(["not", "float"], top_k=5)  # type: ignore


@pytest.mark.asyncio
async def test_upsert_chunks_max_size() -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=PineconeConfig(max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000),
    )

    # We don't actually need to instantiate 10001 chunks, just bypass the type checker
    # and pass a dummy list to check the length validation
    dummy_chunks = [None] * 10001

    with pytest.raises(ValueError, match="Batch size exceeds maximum allowed \\(10000\\)"):
        await client.upsert_chunks(dummy_chunks)  # type: ignore
