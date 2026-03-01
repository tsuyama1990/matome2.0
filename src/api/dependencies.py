from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import httpx
from dependency_injector import containers, providers

from src.core.config import AppSettings
from src.infrastructure.http import HttpxAdapter
from src.infrastructure.llm import OpenRouterClient
from src.infrastructure.storage import LocalStorage
from src.infrastructure.vector_store import PineconeClient


class ConfigContainer(containers.DeclarativeContainer):
    """Container for configuration settings."""

    env = providers.Configuration()
    config = providers.Configuration()
    app_settings = providers.Singleton(AppSettings)


class InfrastructureContainer(containers.DeclarativeContainer):
    """Container for infrastructure dependencies."""

    config_container = providers.DependenciesContainer()

    @staticmethod
    async def init_async_client() -> AsyncGenerator[HttpxAdapter, None]:
        async with httpx.AsyncClient() as client:
            yield HttpxAdapter(client=client)

    http_client = providers.Resource(init_async_client)

    # Infrastructure Implementations
    llm_provider = providers.Factory(
        OpenRouterClient,
        api_key=providers.Callable(
            lambda s: s.openrouter_api_key.get_secret_value(), config_container.app_settings
        ),
        default_model=config_container.app_settings.provided.text_fast_model,
        client=http_client,
        base_url=config_container.app_settings.provided.openrouter_base_url,
    )

    @staticmethod
    def init_pinecone_index(api_key: str, index_name: str) -> Any | None:
        try:
            from pinecone import Pinecone

            pc = Pinecone(api_key=api_key)
            return pc.Index(index_name)
        except Exception:
            return None

    pinecone_index = providers.Singleton(
        init_pinecone_index,
        api_key=providers.Callable(
            lambda s: s.pinecone_api_key.get_secret_value(), config_container.app_settings
        ),
        index_name=config_container.app_settings.provided.pinecone_index_name,
    )

    vector_store = providers.Factory(
        PineconeClient,
        index=pinecone_index,
    )

    file_storage = providers.Factory(
        LocalStorage,
        base_dir=config_container.app_settings.provided.storage_base_dir,
        path_class=Path,
    )


class ApplicationContainer(containers.DeclarativeContainer):
    """Dependency Injection Container assembling sub-containers."""

    config_container = providers.Container(ConfigContainer)
    infrastructure_container = providers.Container(
        InfrastructureContainer,
        config_container=config_container,
    )


class ContainerFactory:
    """Factory to create and initialize the Dependency Injection container."""

    @staticmethod
    def create_container(settings: AppSettings | None = None) -> ApplicationContainer:
        """Creates the container and handles its lifecycle wiring."""
        container = ApplicationContainer()
        if settings:
            # We access the underlying Configuration object logic here
            container.config_container().config.from_pydantic(settings)
            container.config_container().app_settings.override(settings)
        return container
