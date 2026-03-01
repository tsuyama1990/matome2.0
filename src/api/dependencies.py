from dependency_injector import containers, providers

from src.infrastructure.openrouter_llm import OpenRouterLLMProvider
from src.infrastructure.pinecone_vdb import PineconeVectorStore


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["src.api.routers.base", "src.main"])

    config = providers.Configuration()

    llm_provider = providers.Singleton(
        OpenRouterLLMProvider,
    )

    vector_store = providers.Singleton(
        PineconeVectorStore,
    )
