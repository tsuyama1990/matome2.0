from collections.abc import AsyncGenerator

import httpx

from src.domain.ports.http import IHttpClient
from src.domain.ports.llm import ILLMProvider
from src.domain.ports.vector_store import IVectorStore
from src.infrastructure.http import HttpxAdapter
from src.infrastructure.llm import OpenRouterClient, OpenRouterConfig
from src.infrastructure.vector_store import PineconeClient, PineconeIndexProtocol


class VectorStoreFactory:
    """Factory to create VectorStore implementations."""

    @staticmethod
    def create(store_type: str, index: PineconeIndexProtocol) -> IVectorStore:
        if store_type.lower() == "pinecone":
            return PineconeClient(index=index)
        msg = f"Unsupported vector store type: {store_type}"
        raise ValueError(msg)

class LLMClientFactory:
    """Factory to create LLMProvider implementations."""

    @staticmethod
    def create(provider_type: str, config: OpenRouterConfig, http_client: IHttpClient) -> ILLMProvider:
        if provider_type.lower() == "openrouter":
            return OpenRouterClient(config=config, client=http_client)
        msg = f"Unsupported LLM provider type: {provider_type}"
        raise ValueError(msg)

class HTTPClientFactory:
    """Factory to create HTTPClient implementations."""

    @staticmethod
    async def create_async(timeout: float) -> AsyncGenerator[IHttpClient, None]:
        if timeout <= 0:
            raise ValueError("Timeout must be strictly positive")
        client = httpx.AsyncClient(timeout=timeout)
        adapter = HttpxAdapter(client=client)
        try:
            yield adapter
        finally:
            await adapter.close()
