import pytest
from src.api.dependencies import ApplicationContainer
from src.core.config import AppSettings

def test_container_wiring(test_config: AppSettings) -> None:
    """Ensure the container successfully injects and resolves dependencies."""
    container = ApplicationContainer()
    container.app_settings.override(test_config)

    # Resolution should not raise any DI errors like missing arguments or SecretStr evaluation issues
    llm = container.llm_provider()
    assert llm is not None

    vs = container.vector_store()
    assert vs is not None

    storage = container.file_storage()
    assert storage is not None
