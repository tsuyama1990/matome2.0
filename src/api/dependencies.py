from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
from dependency_injector import containers, providers

from src.core.config import AppSettings
from src.infrastructure.http import HttpClientFactory, HttpxAdapter
from src.infrastructure.llm import OpenRouterClientFactory, OpenRouterConfig
from src.infrastructure.storage import StorageFactory
from src.infrastructure.vector_store import PineconeClient, PineconeIndexFactory


class ConfigContainer(containers.DeclarativeContainer):
    """Container for configuration settings."""

    env = providers.Configuration()
    config = providers.Configuration()
    app_settings = providers.Singleton(AppSettings)


class InfrastructureContainer(containers.DeclarativeContainer):
    """Container for infrastructure dependencies."""

    config_settings = providers.Configuration()

    @staticmethod
    async def init_async_client(timeout: float) -> AsyncGenerator[HttpxAdapter, None]:
        client = httpx.AsyncClient(timeout=timeout)
        adapter = HttpClientFactory.create_httpx_adapter(client=client)
        try:
            yield adapter
        finally:
            await adapter.close()

    http_client = providers.Resource(
        init_async_client,
        timeout=config_settings.provided.llm_timeout,
    )

    # Infrastructure Implementations
    llm_config = providers.Factory(
        OpenRouterConfig,
        api_key=providers.Callable(lambda s: s.openrouter_api_key, config_settings),
        default_model=config_settings.provided.text_fast_model,
        base_url=config_settings.provided.openrouter_base_url,
        timeout=config_settings.provided.llm_timeout,
    )

    llm_provider = providers.Factory(
        OpenRouterClientFactory.create_client,
        config=llm_config,
        client=http_client,
    )

    pinecone_index = providers.Singleton(
        PineconeIndexFactory.create_index,
        api_key=providers.Callable(
            lambda s: s.pinecone_api_key.get_secret_value(), config_settings
        ),
        index_name=config_settings.provided.pinecone_index_name,
    )

    vector_store = providers.Factory(
        PineconeClient,
        index=pinecone_index,
    )

    file_storage = providers.Factory(
        StorageFactory.create_local_storage,
        base_dir=config_settings.provided.storage_base_dir,
        path_class=Path,
    )


class ApplicationContainer(containers.DeclarativeContainer):
    """Dependency Injection Container assembling sub-containers."""

    config_container = providers.Container(ConfigContainer)
    infrastructure_container = providers.Container(
        InfrastructureContainer,
        config_settings=config_container.app_settings,
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
