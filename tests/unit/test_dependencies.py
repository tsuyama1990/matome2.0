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


import pytest


@pytest.mark.asyncio
async def test_init_async_client() -> None:
    from src.api.dependencies import InfrastructureContainer

    async_gen = InfrastructureContainer.init_async_client(10.0)
    adapter = await anext(async_gen)

    assert adapter is not None
    assert adapter.client.timeout.read == 10.0

    # We must manually trigger the finally block to ensure cleanup is called
    try:
        await anext(async_gen)
    except StopAsyncIteration:
        pass

    assert adapter.client.is_closed


def test_init_pinecone_index(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    from src.infrastructure.vector_store import PineconeIndexFactory

    mock_pinecone = MagicMock()
    mock_pinecone_instance = MagicMock()
    mock_pinecone.return_value = mock_pinecone_instance
    mock_pinecone_instance.Index.return_value = "MockIndex"

    # Patch the pinecone module that is imported inside the function
    import sys
    import types

    module = types.ModuleType("pinecone")
    module.Pinecone = mock_pinecone  # type: ignore
    sys.modules["pinecone"] = module

    try:
        index = PineconeIndexFactory.create_index("test_key", "test_index")
        assert index == "MockIndex"  # type: ignore[comparison-overlap]
        mock_pinecone.assert_called_once_with(api_key="test_key")
        mock_pinecone_instance.Index.assert_called_once_with("test_index")
    finally:
        del sys.modules["pinecone"]


def test_container_factory_no_settings() -> None:
    container = ContainerFactory.create_container()
    assert container is not None

    # Check default behavior when initialized without overrides
    assert container.config_container.app_settings is not None
