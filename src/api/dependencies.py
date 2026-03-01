from collections.abc import AsyncGenerator

from dependency_injector import containers, providers

from src.core.config import AppSettings
from src.infrastructure.openrouter_llm import OpenRouterLLMProvider
from src.infrastructure.pinecone_vdb import PineconeVectorStore


async def init_llm_provider(
    api_key: str, max_keepalive: int, max_connections: int
) -> AsyncGenerator[OpenRouterLLMProvider, None]:
    provider = OpenRouterLLMProvider(
        api_key=api_key, max_keepalive=max_keepalive, max_connections=max_connections
    )
    yield provider
    await provider.close()


async def init_vector_store(
    api_url: str, max_keepalive: int, max_connections: int
) -> AsyncGenerator[PineconeVectorStore, None]:
    store = PineconeVectorStore(
        api_url=api_url, max_keepalive=max_keepalive, max_connections=max_connections
    )
    yield store
    await store.close()


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["src.api.routers.base", "src.main"])

    # Provide configuration using our AppSettings schema to enforce validation on start
    config = providers.Singleton(AppSettings)

    llm_provider = providers.Resource(
        init_llm_provider,
        api_key=config.provided.OPENROUTER_API_KEY,
        max_keepalive=config.provided.MAX_KEEPALIVE_CONNECTIONS,
        max_connections=config.provided.MAX_CONNECTIONS,
    )

    vector_store = providers.Resource(
        init_vector_store,
        api_url=config.provided.VECTOR_DB_URL,
        max_keepalive=config.provided.MAX_KEEPALIVE_CONNECTIONS,
        max_connections=config.provided.MAX_CONNECTIONS,
    )
