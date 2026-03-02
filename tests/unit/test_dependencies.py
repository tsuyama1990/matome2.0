
from src.api.dependencies import ContainerFactory
from src.core.config import AppSettings


def test_container_wiring(test_config: AppSettings) -> None:
    """Ensure the container successfully injects and resolves dependencies."""
    container = ContainerFactory.create_container(test_config)

    # Resolution should not raise any DI errors like missing arguments or SecretStr evaluation issues
    llm = container.infrastructure_container.llm_provider()
    assert llm is not None

    vs = container.infrastructure_container.vector_store()
    assert vs is not None

    storage = container.infrastructure_container.file_storage()
    assert storage is not None
