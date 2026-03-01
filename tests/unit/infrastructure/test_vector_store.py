from collections.abc import Generator
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.domain.models.document import DocumentChunk
from src.infrastructure.vector_store import PineconeClient


@pytest.fixture
def mock_pinecone() -> Generator[MagicMock, None, None]:
    with patch("src.infrastructure.vector_store.Pinecone") as MockPinecone:
        mock_pc = MockPinecone.return_value
        mock_index = MagicMock()
        mock_pc.Index.return_value = mock_index
        yield mock_index


@pytest.fixture
def mock_pinecone_class(mock_pinecone: MagicMock) -> MagicMock:
    pc_class = MagicMock()
    # Mocking the initialization such that calling pc_class(api_key="...") returns an object
    # that has an `Index` method, which when called returns our `mock_pinecone` mock.
    pc_instance = MagicMock()
    pc_instance.Index.return_value = mock_pinecone
    pc_class.return_value = pc_instance
    return pc_class


@pytest.fixture
def vector_client(mock_pinecone_class: MagicMock) -> PineconeClient:
    return PineconeClient(api_key="dummy_key", pinecone_class=mock_pinecone_class)


@pytest.mark.asyncio
async def test_check_health(vector_client: PineconeClient) -> None:
    assert await vector_client.check_health() is True


@pytest.mark.asyncio
async def test_check_health_failure() -> None:
    pc_class = MagicMock(side_effect=Exception("Init failed"))
    client = PineconeClient(api_key="dummy_key", pinecone_class=pc_class)
    assert await client.check_health() is False


@pytest.mark.asyncio
async def test_upsert_chunks_success(
    vector_client: PineconeClient, mock_pinecone: MagicMock
) -> None:
    chunk = DocumentChunk(
        chunk_id=uuid4(), document_id=uuid4(), text="Test", embedding=[0.1, 0.2, 0.3]
    )

    await vector_client.upsert_chunks([chunk])
    mock_pinecone.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_chunks_missing_embedding(vector_client: PineconeClient) -> None:
    chunk = DocumentChunk(chunk_id=uuid4(), document_id=uuid4(), text="Test", embedding=None)

    with pytest.raises(ValueError, match="has no embedding"):
        await vector_client.upsert_chunks([chunk])


@pytest.mark.asyncio
async def test_search_similar_success(
    vector_client: PineconeClient, mock_pinecone: MagicMock
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
    mock_pinecone.query.return_value = mock_response

    results = await vector_client.search_similar(query_embedding=[0.1, 0.2, 0.3])

    assert len(results) == 1
    assert results[0].text == "Test result"
    assert results[0].metadata["extra_meta"] == "value"


@pytest.mark.asyncio
async def test_search_similar_connection_error(
    vector_client: PineconeClient, mock_pinecone: MagicMock
) -> None:
    mock_pinecone.query.side_effect = Exception("Network down")

    with pytest.raises(ConnectionError, match="Pinecone query failed"):
        await vector_client.search_similar(query_embedding=[0.1, 0.2, 0.3])
