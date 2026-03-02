from src.api.dependencies import ContainerFactory
from src.core.config import AppSettings


def test_container_wiring(test_config: AppSettings) -> None:
    """Ensure the container successfully injects and resolves dependencies."""
    container = ContainerFactory.create_container(test_config)

    # Resolution should not raise any DI errors like missing arguments or SecretStr evaluation issues
    llm = container.infrastructure_container.llm_provider()
    assert llm is not None

    from unittest.mock import MagicMock

    from dependency_injector import providers

    # Safely override the dependency so it doesn't try to initialize the real pinecone index
    # which would otherwise fail because test keys aren't valid Pinecone formats
    container.infrastructure_container.pinecone_index.override(providers.Object(MagicMock()))
    vs = container.infrastructure_container.vector_store()
    assert vs is not None
    container.infrastructure_container.pinecone_index.reset_override()

    storage = container.infrastructure_container.file_storage()
    assert storage is not None
