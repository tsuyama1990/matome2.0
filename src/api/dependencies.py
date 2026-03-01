from dependency_injector import containers, providers

from src.core.config import AppSettings


class ApplicationContainer(containers.DeclarativeContainer):
    """Dependency Injection Container for application."""

    wiring_config = containers.WiringConfiguration(modules=["main"])
    config = providers.Configuration()
    app_settings = providers.Singleton(AppSettings)

    # In future cycles, concrete implementations of ILLMProvider,
    # IVectorStore, and IFileStorage will be configured here.
