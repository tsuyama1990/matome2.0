import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.domain.exceptions import ConfigurationError
from src.domain.models.document import DocumentChunk
from src.infrastructure.vector_store import PineconeClient, PineconeConfig, PineconeIndexProtocol, PineconeIndexAdapter


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
async def test_check_health_with_timeout(vector_client: PineconeClient) -> None:
    assert await vector_client.check_health(timeout=1.0) is True


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

    with pytest.raises(ValueError, match="has invalid or missing embedding"):
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
        "extra_meta": "value",
    }

    mock_response = MagicMock()
    mock_response.matches = [mock_match]
    mock_pinecone_index.query.return_value = mock_response

    results = await vector_client.search_similar(query_embedding=[0.1, 0.2, 0.3], top_k=5)

    assert len(results) == 1
    assert results[0].text == ""
    assert results[0].metadata["extra_meta"] == "value"


@pytest.mark.asyncio
async def test_search_similar_connection_error(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    mock_pinecone_index.query.side_effect = Exception("Network down")

    with pytest.raises(ConnectionError, match="ERR_PINECONE_SEARCH_01"):
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
        with pytest.raises(ConnectionError, match="ERR_PINECONE_UPSERT_01"):
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
        "extra_meta": "value",
    }

    mock_response = MagicMock()
    mock_response.matches = [mock_match]

    mock_pinecone_index.query.side_effect = [Exception("Network down"), mock_response]

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        results = await vector_client.search_similar(query_embedding=[0.1, 0.2, 0.3], top_k=5)

    assert len(results) == 1
    assert results[0].text == ""
    assert mock_pinecone_index.query.call_count == 2


@pytest.mark.asyncio
async def test_search_similar_retry_failure(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    mock_pinecone_index.query.side_effect = Exception("Network down")

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        with pytest.raises(ConnectionError, match="ERR_PINECONE_SEARCH_01"):
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
        ValueError, match="query_embedding must be a valid list"
    ):
        await client.search_similar([], top_k=5)

    with pytest.raises(
        ValueError, match="query_embedding must contain only numeric values"
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

def test_pinecone_index_adapter_upsert():
    mock_index = MagicMock()
    adapter = PineconeIndexAdapter(mock_index)
    adapter.upsert([{"id": "1", "values": [0.1]}])
    mock_index.upsert.assert_called_once_with(vectors=[{"id": "1", "values": [0.1]}])

def test_pinecone_index_adapter_query_object():
    mock_index = MagicMock()

    class MockResponse:
        def to_dict(self):
            return {"matches": []}

    mock_index.query.return_value = MockResponse()
    adapter = PineconeIndexAdapter(mock_index)
    res = adapter.query(vector=[0.1], top_k=5, filter_dict=None, include_metadata=True)
    assert res == {"matches": []}

def test_pinecone_index_adapter_query_dict():
    mock_index = MagicMock()
    mock_index.query.return_value = {"matches": []}
    adapter = PineconeIndexAdapter(mock_index)
    res = adapter.query(vector=[0.1], top_k=5, filter_dict=None, include_metadata=True)
    assert res == {"matches": []}

def test_pinecone_index_adapter_describe_stats_object():
    mock_index = MagicMock()
    class MockStats:
        def to_dict(self):
            return {"dimension": 1536}

    mock_index.describe_index_stats.return_value = MockStats()
    adapter = PineconeIndexAdapter(mock_index)
    res = adapter.describe_index_stats()
    assert res == {"dimension": 1536}

def test_pinecone_index_adapter_describe_stats_dict():
    mock_index = MagicMock()
    mock_index.describe_index_stats.return_value = {"dimension": 1536}
    adapter = PineconeIndexAdapter(mock_index)
    res = adapter.describe_index_stats()
    assert res == {"dimension": 1536}

@pytest.mark.asyncio
async def test_search_similar_handles_dict_response():
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=PineconeConfig(max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000),
    )

    mock_index.query.return_value = {
        "matches": [
            {
                "id": str(uuid4()),
                "values": [0.1, 0.2, 0.3],
                "metadata": {"text": "dict match"}
            },
            {
                # Missing id, values, metadata
            }
        ]
    }

    res = await client.search_similar(query_embedding=[0.1], top_k=2)
    assert len(res) == 2
    assert res[0].text == ""  # text is dropped intentionally per security
    assert res[1].text == ""
    assert res[1].embedding is None

@pytest.mark.asyncio
async def test_search_similar_handles_missing_matches():
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=PineconeConfig(max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000),
    )

    mock_index.query.return_value = {}

    res = await client.search_similar(query_embedding=[0.1], top_k=2)
    assert len(res) == 0

@pytest.mark.asyncio
async def test_search_similar_handles_object_with_none_matches():
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=PineconeConfig(max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000),
    )

    class MockResponse:
        matches = None

    mock_index.query.return_value = MockResponse()

    res = await client.search_similar(query_embedding=[0.1], top_k=2)
    assert len(res) == 0

@pytest.mark.asyncio
async def test_search_similar_handles_object_missing_attributes():
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=PineconeConfig(max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000),
    )

    class MockMatch:
        id = None
        values = None
        metadata = None

    class MockMatchWithMethod:
        id = None
        def values(self):
            return [0.1]
        metadata = None

    class MockMatchWithDictId:
        id = {"id": "test"} # should fail parsing
        values = None
        metadata = {"document_id": ""}

    class MockMatchWithBadId:
        id = "not-a-uuid"
        values = None
        metadata = {"document_id": "not-a-uuid"}

    class MockResponse:
        matches = [
            MockMatch(),
            MockMatchWithMethod(),
            {"id": None, "values": None, "metadata": None},
            MockMatchWithDictId(),
            {"id": "test", "values": None, "metadata": {"document_id": None}},
            MockMatchWithBadId(),
            {"id": "test", "values": None, "metadata": {"document_id": ""}},
            {"id": "test2", "values": None, "metadata": {"document_id": "not-a-uuid"}}
        ]

    mock_index.query.return_value = MockResponse()

    res = await client.search_similar(query_embedding=[0.1], top_k=8)
    assert len(res) == 8
    assert res[0].text == ""
    assert res[0].embedding is None
    assert res[1].embedding is None
    assert res[2].embedding is None
    assert res[3].embedding is None
    assert str(res[3].document_id) == "00000000-0000-0000-0000-000000000000"
    assert str(res[4].document_id) == "00000000-0000-0000-0000-000000000000"
    assert str(res[5].document_id) == "00000000-0000-0000-0000-000000000000"
    assert str(res[6].document_id) == "00000000-0000-0000-0000-000000000000"
    assert str(res[7].document_id) == "00000000-0000-0000-0000-000000000000"

    # Add coverage for valid id missing from missing test
    class MockMatchValidID:
        id = "202e8d91-a1dc-49e0-8438-2a74c2dfd1d6"
        values = None
        metadata = None

    mock_index.query.return_value = {"matches": [MockMatchValidID()]}
    res2 = await client.search_similar(query_embedding=[0.1], top_k=1)
    assert str(res2[0].chunk_id) == "202e8d91-a1dc-49e0-8438-2a74c2dfd1d6"


def test_pinecone_index_factory():
    from src.infrastructure.vector_store import PineconeIndexFactory
    with pytest.MonkeyPatch().context() as m:
        class MockIndex:
            pass
        class MockPinecone:
            def __init__(self, api_key):
                self.api_key = api_key
            def Index(self, index_name):
                return MockIndex()

        import sys
        mock_pinecone_module = MagicMock()
        mock_pinecone_module.Pinecone = MockPinecone
        m.setitem(sys.modules, "pinecone", mock_pinecone_module)

        # Valid key needs alphanumeric, hyphens, and > 30 chars
        valid_key = "a" * 35
        index = PineconeIndexFactory.create_index(valid_key, "fake_name")
        assert isinstance(index, PineconeIndexAdapter)

def test_pinecone_index_factory_invalid_key():
    from src.infrastructure.vector_store import PineconeIndexFactory
    with pytest.raises(ValueError, match="ERR_INVALID_PINECONE_API_KEY_FORMAT"):
        PineconeIndexFactory.create_index("", "fake_name")

def test_vector_store_factory():
    from src.infrastructure.vector_store import VectorStoreFactory
    mock_index = MagicMock()
    config = PineconeConfig(max_retries=1, base_delay=1.0, batch_size=1, max_batch_size=1)
    client = VectorStoreFactory.create_pinecone_client(mock_index, config)
    assert isinstance(client, PineconeClient)


def test_pinecone_index_adapter_upsert_exception():
    mock_index = MagicMock()
    mock_index.upsert.side_effect = Exception("failed")
    adapter = PineconeIndexAdapter(mock_index)
    with pytest.raises(ConnectionError):
        adapter.upsert([])

def test_pinecone_index_adapter_query_exception():
    mock_index = MagicMock()
    mock_index.query.side_effect = Exception("failed")
    adapter = PineconeIndexAdapter(mock_index)
    with pytest.raises(ConnectionError):
        adapter.query(vector=[0.1], top_k=5, filter_dict=None, include_metadata=True)

def test_pinecone_index_adapter_describe_stats_exception():
    mock_index = MagicMock()
    mock_index.describe_index_stats.side_effect = Exception("failed")
    adapter = PineconeIndexAdapter(mock_index)
    with pytest.raises(ConnectionError):
        adapter.describe_index_stats()

@pytest.mark.asyncio
async def test_upsert_chunks_empty_chunks(vector_client: PineconeClient) -> None:
    await vector_client.upsert_chunks([])

@pytest.mark.asyncio
async def test_upsert_chunks_invalid_embedding_empty(vector_client: PineconeClient) -> None:
    chunk = DocumentChunk(chunk_id=uuid4(), document_id=uuid4(), text="Test", embedding=[])
    with pytest.raises(ValueError, match="has empty embedding"):
        await vector_client.upsert_chunks([chunk])


@pytest.mark.asyncio
async def test_upsert_chunks_invalid_metadata(vector_client: PineconeClient) -> None:
    chunk = DocumentChunk(chunk_id=uuid4(), document_id=uuid4(), text="Test", embedding=[0.1], metadata={"valid": "ok", "invalid": []})
    await vector_client.upsert_chunks([chunk])

@pytest.mark.asyncio
async def test_upsert_chunks_empty_list_return(vector_client: PineconeClient) -> None:
    await vector_client.upsert_chunks([])
