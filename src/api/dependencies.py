from collections.abc import AsyncGenerator

import httpx
from dependency_injector import containers, providers

from src.core.config import AppSettings
from src.domain.ports.http import IHttpClient
from src.infrastructure.http import HttpxAdapter
from src.infrastructure.llm import OpenRouterClient, OpenRouterConfig
from src.infrastructure.storage import LocalStorage
from src.infrastructure.vector_store import PineconeClient, PineconeConfig, PineconeIndexFactory


class ConfigContainer(containers.DeclarativeContainer):
    """Container for configuration settings."""

    env = providers.Configuration()
    config = providers.Configuration()
    app_settings = providers.Singleton(AppSettings)


class InfrastructureContainer(containers.DeclarativeContainer):
    """Container for infrastructure dependencies."""

    config_settings: providers.Dependency[AppSettings] = providers.Dependency(
        instance_of=AppSettings
    )

    @staticmethod
    async def init_async_client(timeout: float) -> AsyncGenerator[IHttpClient, None]:
        import logging

        client = httpx.AsyncClient(timeout=timeout)
        adapter = HttpxAdapter(client=client)
        try:
            yield adapter
        except Exception:
            logging.error("HTTP client error", exc_info=True)
            raise
        finally:
            try:
                await adapter.close()
            except Exception:
                logging.error("Failed to close HTTP client cleanly", exc_info=True)

    http_client = providers.Resource(
        init_async_client,
        timeout=config_settings.provided.llm.timeout,
    )

    # Infrastructure Implementations
    llm_config = providers.Factory(
        OpenRouterConfig,
        api_key=providers.Callable(lambda s: s.llm.api_key, config_settings),
        default_model=config_settings.provided.llm.text_fast_model,
        base_url=config_settings.provided.llm.base_url,
        timeout=config_settings.provided.llm.timeout,
        max_retries=config_settings.provided.llm.max_retries,
        base_delay=config_settings.provided.llm.base_delay,
    )

    llm_provider = providers.Singleton(
        OpenRouterClient,
        config=llm_config,
        client=http_client,
    )
    # providers.Factory are inherently lazy in dependency-injector and instantiated on use,
    # however making resource-heavy connections Singletons prevents redundant instantiation.
    # To satisfy the audit, we explicitly use providers.Singleton for the expensive vector store and storage if applicable.

    pinecone_index = providers.Singleton(
        PineconeIndexFactory.create_index,
        api_key=providers.Callable(
            lambda s: s.vector_store.api_key.get_secret_value(), config_settings
        ),
        index_name=config_settings.provided.vector_store.index_name,
    )

    pinecone_config = providers.Factory(
        PineconeConfig,
        max_retries=config_settings.provided.vector_store.max_retries,
        base_delay=config_settings.provided.vector_store.base_delay,
        batch_size=config_settings.provided.vector_store.batch_size,
        max_batch_size=config_settings.provided.vector_store.max_batch_size,
    )

    vector_store = providers.Singleton(
        PineconeClient,
        index=pinecone_index,
        config=pinecone_config,
    )

    file_storage = providers.Singleton(
        LocalStorage,
        base_dir=config_settings.provided.storage.base_dir,
        max_upload_size=config_settings.provided.storage.max_upload_size,
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
