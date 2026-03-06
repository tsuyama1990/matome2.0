import asyncio
import typing
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.core.constants import (
    ERR_EMBEDDING_CANNOT_BE_EMPTY,
    ERR_EMBEDDING_MUST_BE_LIST,
    ERR_EMBEDDING_MUST_BE_NUMERIC,
    ERR_EMPTY_EMBEDDING,
    ERR_INVALID_OR_MISSING_EMBEDDING,
    ERR_INVALID_PINECONE_API_KEY_FORMAT,
    ERR_PINECONE_SEARCH_01,
    ERR_PINECONE_UPSERT_01,
)
from src.domain.exceptions import ConfigurationError
from src.infrastructure.vector_store import (
    PineconeClient,
    PineconeConfig,
    PineconeIndexAdapter,
    PineconeIndexProtocol,
)
from tests.unit.infrastructure.test_data_factory import TestDataFactory


@pytest.fixture
def mock_pinecone_index() -> MagicMock:
    return MagicMock()


@pytest.fixture
def test_config() -> PineconeConfig:
    return PineconeConfig(max_retries=3, base_delay=1.0, batch_size=100, max_batch_size=10000)


@pytest.fixture
def vector_client(mock_pinecone_index: MagicMock, test_config: PineconeConfig) -> PineconeClient:
    return PineconeClient(
        index=mock_pinecone_index,
        config=test_config,
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
    chunk = TestDataFactory.create_mock_chunk()

    await vector_client.upsert_chunks([chunk])
    mock_pinecone_index.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_chunks_missing_embedding(vector_client: PineconeClient) -> None:
    chunk = TestDataFactory.create_mock_chunk()
    chunk = chunk.model_copy(update={"embedding": None})

    with pytest.raises(ValueError, match=ERR_INVALID_OR_MISSING_EMBEDDING.split("{")[0]):
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

    with pytest.raises(ConnectionError, match=ERR_PINECONE_SEARCH_01):
        await vector_client.search_similar(query_embedding=[0.1, 0.2, 0.3], top_k=5)


@pytest.mark.asyncio
async def test_upsert_chunks_retry_success(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    chunk = TestDataFactory.create_mock_chunk()

    mock_pinecone_index.upsert.side_effect = [Exception("Network down"), None]

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        await vector_client.upsert_chunks([chunk])
    assert mock_pinecone_index.upsert.call_count == 2


@pytest.mark.asyncio
async def test_upsert_chunks_retry_failure(
    vector_client: PineconeClient, mock_pinecone_index: MagicMock
) -> None:
    chunk = TestDataFactory.create_mock_chunk()

    mock_pinecone_index.upsert.side_effect = Exception("Network down")

    with pytest.MonkeyPatch().context() as m:
        m.setattr(asyncio, "sleep", AsyncMock())
        with pytest.raises(ConnectionError, match=ERR_PINECONE_UPSERT_01):
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
        with pytest.raises(ConnectionError, match=ERR_PINECONE_SEARCH_01):
            await vector_client.search_similar(query_embedding=[0.1, 0.2, 0.3], top_k=5)

    assert mock_pinecone_index.query.call_count == 3


@pytest.mark.asyncio
async def test_check_health_exception(test_config: PineconeConfig) -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    mock_index.describe_index_stats.side_effect = Exception("failed")
    client = PineconeClient(
        index=mock_index,
        config=test_config,
    )

    assert await client.check_health() is False


@pytest.mark.asyncio
async def test_upsert_chunks_batching(test_config: PineconeConfig) -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=test_config,
    )

    chunks = []
    for _ in range(150):  # > 100 to trigger batching loop
        chunks.append(TestDataFactory.create_mock_chunk())

    await client.upsert_chunks(chunks)
    assert mock_index.upsert.call_count == 2


@pytest.mark.asyncio
async def test_search_similar_invalid_query(test_config: PineconeConfig) -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=test_config,
    )

    with pytest.raises(TypeError, match=ERR_EMBEDDING_MUST_BE_LIST):
        await client.search_similar(None, top_k=5)  # type: ignore

    with pytest.raises(ValueError, match=ERR_EMBEDDING_CANNOT_BE_EMPTY):
        await client.search_similar(TestDataFactory.get_empty_list(), top_k=5)

    with pytest.raises(ValueError, match=ERR_EMBEDDING_MUST_BE_NUMERIC):
        await client.search_similar(TestDataFactory.get_invalid_embedding(), top_k=5)


@pytest.mark.asyncio
async def test_upsert_chunks_max_size(test_config: PineconeConfig) -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=test_config,
    )

    # We don't actually need to instantiate 10001 chunks, just bypass the type checker
    # and pass a dummy list to check the length validation
    dummy_chunks = [None] * 10001

    with pytest.raises(ValueError, match="Batch size exceeds maximum allowed \\(10000\\)"):
        await client.upsert_chunks(dummy_chunks)  # type: ignore


def test_pinecone_index_adapter_upsert() -> None:
    mock_index = MagicMock()
    adapter = PineconeIndexAdapter(mock_index)
    adapter.upsert([{"id": "1", "values": [0.1]}])
    mock_index.upsert.assert_called_once_with(vectors=[{"id": "1", "values": [0.1]}])


def test_pinecone_index_adapter_query_object() -> None:
    mock_index = MagicMock()

    class MockResponse:
        def to_dict(self) -> dict[str, Any]:
            return {"matches": []}

    mock_index.query.return_value = MockResponse()
    adapter = PineconeIndexAdapter(mock_index)
    res = adapter.query(vector=[0.1], top_k=5, filter_dict=None, include_metadata=True)
    assert res == {"matches": []}


def test_pinecone_index_adapter_query_dict() -> None:
    mock_index = MagicMock()
    mock_index.query.return_value = {"matches": []}
    adapter = PineconeIndexAdapter(mock_index)
    res = adapter.query(vector=[0.1], top_k=5, filter_dict=None, include_metadata=True)
    assert res == {"matches": []}


def test_pinecone_index_adapter_describe_stats_object() -> None:
    mock_index = MagicMock()

    class MockStats:
        def to_dict(self) -> dict[str, Any]:
            return {"dimension": 1536}

    mock_index.describe_index_stats.return_value = MockStats()
    adapter = PineconeIndexAdapter(mock_index)
    res = adapter.describe_index_stats()
    assert res == {"dimension": 1536}


def test_pinecone_index_adapter_describe_stats_dict() -> None:
    mock_index = MagicMock()
    mock_index.describe_index_stats.return_value = {"dimension": 1536}
    adapter = PineconeIndexAdapter(mock_index)
    res = adapter.describe_index_stats()
    assert res == {"dimension": 1536}


@pytest.mark.asyncio
async def test_search_similar_handles_dict_response(test_config: PineconeConfig) -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=test_config,
    )

    mock_index.query.return_value = {
        "matches": [
            {"id": str(uuid4()), "values": [0.1, 0.2, 0.3], "metadata": {"text": "dict match"}},
            {
                # Missing id, values, metadata
            },
        ]
    }

    res = await client.search_similar(query_embedding=[0.1], top_k=2)
    assert len(res) == 2
    assert res[0].text == ""  # text is dropped intentionally per security
    assert res[1].text == ""
    assert res[1].embedding is None


@pytest.mark.asyncio
async def test_search_similar_handles_missing_matches(test_config: PineconeConfig) -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=test_config,
    )

    mock_index.query.return_value = {}

    res = await client.search_similar(query_embedding=[0.1], top_k=2)
    assert len(res) == 0


@pytest.mark.asyncio
async def test_search_similar_handles_object_with_none_matches(test_config: PineconeConfig) -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=test_config,
    )

    class MockResponse:
        matches = None

    mock_index.query.return_value = MockResponse()

    res = await client.search_similar(query_embedding=[0.1], top_k=2)
    assert len(res) == 0


@pytest.mark.asyncio
async def test_search_similar_handles_object_missing_attributes(
    test_config: PineconeConfig,
) -> None:
    mock_index = MagicMock(spec=PineconeIndexProtocol)
    client = PineconeClient(
        index=mock_index,
        config=test_config,
    )

    class MockMatch:
        id = None
        values = None
        metadata = None

    class MockMatchWithMethod:
        id = None

        def values(self) -> list[float]:
            return [0.1]

        metadata = None

    class MockMatchWithDictId:
        id: typing.ClassVar = {"id": "test"}  # should fail parsing
        values: typing.ClassVar = None
        metadata: typing.ClassVar = {"document_id": ""}

    class MockMatchWithBadId:
        id: typing.ClassVar = "not-a-uuid"
        values: typing.ClassVar = None
        metadata: typing.ClassVar = {"document_id": "not-a-uuid"}

    class MockResponse:
        matches: typing.ClassVar = [
            MockMatch(),
            MockMatchWithMethod(),
            {"id": None, "values": None, "metadata": None},
            MockMatchWithDictId(),
            {"id": "test", "values": None, "metadata": {"document_id": None}},
            MockMatchWithBadId(),
            {"id": "test", "values": None, "metadata": {"document_id": ""}},
            {"id": "test2", "values": None, "metadata": {"document_id": "not-a-uuid"}},
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


def test_pinecone_index_factory() -> None:
    from src.infrastructure.vector_store import PineconeIndexFactory

    with pytest.MonkeyPatch().context() as m:

        class MockIndex:
            pass

        class MockPinecone:
            def __init__(self, api_key: str) -> None:
                self.api_key = api_key

            def Index(self, index_name: str) -> Any:  # noqa: N802
                return MockIndex()

        import sys

        mock_pinecone_module = MagicMock()
        mock_pinecone_module.Pinecone = MockPinecone
        m.setitem(sys.modules, "pinecone", mock_pinecone_module)

        # Valid key needs alphanumeric, hyphens, and > 30 chars
        valid_key = TestDataFactory.get_valid_api_key()
        index = PineconeIndexFactory.create_index(valid_key, "fake_name")
        assert isinstance(index, PineconeIndexAdapter)


def test_pinecone_index_factory_invalid_key() -> None:
    from src.infrastructure.vector_store import PineconeIndexFactory

    with pytest.raises(ValueError, match=ERR_INVALID_PINECONE_API_KEY_FORMAT):
        PineconeIndexFactory.create_index(TestDataFactory.get_invalid_api_key(), "fake_name")


def test_vector_store_factory() -> None:
    from src.infrastructure.vector_store import VectorStoreFactory

    mock_index = MagicMock()
    config = PineconeConfig(max_retries=1, base_delay=1.0, batch_size=1, max_batch_size=1)
    client = VectorStoreFactory.create_pinecone_client(mock_index, config)
    assert isinstance(client, PineconeClient)


def test_pinecone_index_adapter_upsert_exception() -> None:
    mock_index = MagicMock()
    mock_index.upsert.side_effect = Exception("failed")
    adapter = PineconeIndexAdapter(mock_index)
    with pytest.raises(ConnectionError):
        adapter.upsert([])


def test_pinecone_index_adapter_query_exception() -> None:
    mock_index = MagicMock()
    mock_index.query.side_effect = Exception("failed")
    adapter = PineconeIndexAdapter(mock_index)
    with pytest.raises(ConnectionError):
        adapter.query(vector=[0.1], top_k=5, filter_dict=None, include_metadata=True)


def test_pinecone_index_adapter_describe_stats_exception() -> None:
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
    chunk = TestDataFactory.create_mock_chunk()
    chunk = chunk.model_copy(update={"embedding": []})
    with pytest.raises(ValueError, match=ERR_EMPTY_EMBEDDING.split("{")[0]):
        await vector_client.upsert_chunks([chunk])


@pytest.mark.asyncio
async def test_upsert_chunks_invalid_metadata(vector_client: PineconeClient) -> None:
    chunk = TestDataFactory.create_mock_chunk()
    chunk = chunk.model_copy(update={"metadata": {"valid": "ok", "invalid": []}})
    await vector_client.upsert_chunks([chunk])


@pytest.mark.asyncio
async def test_upsert_chunks_empty_list_return(vector_client: PineconeClient) -> None:
    await vector_client.upsert_chunks([])
