from unittest.mock import MagicMock

import pytest

from src.infrastructure.factories import HTTPClientFactory, LLMClientFactory, VectorStoreFactory
from src.infrastructure.llm import OpenRouterClient
from src.infrastructure.vector_store import PineconeClient


def test_vector_store_factory() -> None:
    mock_index = MagicMock()
    vs = VectorStoreFactory.create("pinecone", mock_index)
    assert isinstance(vs, PineconeClient)

    with pytest.raises(ValueError, match="Unsupported vector store type: invalid"):
        VectorStoreFactory.create("invalid", mock_index)

def test_llm_client_factory() -> None:
    mock_config = MagicMock()
    mock_config.base_url = "https://openrouter.ai"
    mock_http = MagicMock()
    llm = LLMClientFactory.create("openrouter", mock_config, mock_http)
    assert isinstance(llm, OpenRouterClient)

    with pytest.raises(ValueError, match="Unsupported LLM provider type: invalid"):
        LLMClientFactory.create("invalid", mock_config, mock_http)


@pytest.mark.asyncio
async def test_http_client_factory_error() -> None:
    with pytest.raises(ValueError, match="Timeout must be strictly positive"):
        async for _ in HTTPClientFactory.create_async(-1):
            pass

@pytest.mark.asyncio
async def test_http_client_factory_success() -> None:
    async for client in HTTPClientFactory.create_async(10.0):
        assert client is not None
