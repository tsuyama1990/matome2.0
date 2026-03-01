from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
from dependency_injector import containers, providers

from src.core.config import AppSettings
from src.infrastructure.llm import OpenRouterClient
from src.infrastructure.storage import LocalStorage
from src.infrastructure.vector_store import PineconeClient


class ApplicationContainer(containers.DeclarativeContainer):
    """Dependency Injection Container for application."""

    env = providers.Configuration()
    config = providers.Configuration()
    app_settings = providers.Singleton(AppSettings)

    @staticmethod
    async def init_async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
        async with httpx.AsyncClient() as client:
            yield client

    http_client = providers.Resource(init_async_client)

    # Infrastructure Implementations
    llm_provider = providers.Factory(
        OpenRouterClient,
        api_key=providers.Callable(lambda s: s.openrouter_api_key.get_secret_value(), app_settings),
        default_model=app_settings.provided.text_fast_model,
        client=http_client,
        base_url=app_settings.provided.openrouter_base_url,
    )

    vector_store = providers.Factory(
        PineconeClient,
        api_key=providers.Callable(lambda s: s.pinecone_api_key.get_secret_value(), app_settings),
    )

    file_storage = providers.Factory(
        LocalStorage,
        base_dir=Path("./data"),  # Default storage directory
        path_class=Path,
    )


class ContainerFactory:
    """Factory to create and initialize the Dependency Injection container."""

    @staticmethod
    def create_container(settings: AppSettings | None = None) -> ApplicationContainer:
        """Creates the container and handles its lifecycle wiring."""
        container = ApplicationContainer()
        if settings:
            container.config.from_pydantic(settings)
            container.app_settings.override(settings)
        return container
