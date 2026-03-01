from pathlib import Path

from dependency_injector import containers, providers

from src.core.config import AppSettings
from src.infrastructure.llm import OpenRouterClient
from src.infrastructure.storage import LocalStorage
from src.infrastructure.vector_store import PineconeClient


class ApplicationContainer(containers.DeclarativeContainer):
    """Dependency Injection Container for application."""

    config = providers.Configuration()
    app_settings = providers.Singleton(AppSettings)

    # Infrastructure Implementations
    llm_provider = providers.Factory(
        OpenRouterClient,
        api_key=providers.Callable(lambda s: s.openrouter_api_key.get_secret_value(), app_settings),
        default_model=app_settings.provided.text_fast_model,
    )

    vector_store = providers.Factory(
        PineconeClient,
        api_key=providers.Callable(lambda s: s.pinecone_api_key.get_secret_value(), app_settings),
    )

    file_storage = providers.Factory(
        LocalStorage,
        base_dir=Path("./data"),  # Default storage directory
    )
