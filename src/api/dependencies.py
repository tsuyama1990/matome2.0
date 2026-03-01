from pathlib import Path

from dependency_injector import containers, providers

from src.core.config import AppSettings
from src.infrastructure.llm import OpenRouterClient
from src.infrastructure.storage import LocalStorage
from src.infrastructure.vector_store import PineconeClient


class ApplicationContainer(containers.DeclarativeContainer):
    """Dependency Injection Container for application."""

    wiring_config = containers.WiringConfiguration(modules=["main"])
    config = providers.Configuration()
    app_settings = providers.Singleton(AppSettings)

    # Infrastructure Implementations
    llm_provider = providers.Factory(
        OpenRouterClient,
        api_key=app_settings.provided.openrouter_api_key,
        default_model=app_settings.provided.text_fast_model,
    )

    vector_store = providers.Factory(
        PineconeClient,
        api_key=app_settings.provided.pinecone_api_key,
    )

    file_storage = providers.Factory(
        LocalStorage,
        base_dir=Path("./data"),  # Default storage directory
    )
