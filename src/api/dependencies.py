from dependency_injector import containers, providers

from src.domain_models.chunk import SemanticChunk
from src.infrastructure.llm_interface import ILLMProvider
from src.infrastructure.vdb_interface import IVectorStore


# Dummy implementations for injection
class DummyLLMProvider(ILLMProvider):
    async def generate_completion(self, prompt: str) -> str:
        return ""


class DummyVectorStore(IVectorStore):
    async def upsert_chunks(self, chunks: list[SemanticChunk]) -> bool:
        return True

    async def upsert_chunks_batch(
        self, chunks: list[SemanticChunk], batch_size: int = 1000
    ) -> bool:
        return True

    async def stream_chunks_to_store(self, document_id: str, document_path: str) -> None:
        pass

    async def search(
        self, query_vector: list[float], limit: int, offset: int = 0
    ) -> list[SemanticChunk]:
        return []

    async def search_batch(
        self, query_vectors: list[list[float]], limit: int, offset: int = 0
    ) -> list[list[SemanticChunk]]:
        return []


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["src.api.routers.base", "src.main"])

    config = providers.Configuration()

    llm_provider = providers.Singleton(
        DummyLLMProvider,
    )

    vector_store = providers.Singleton(
        DummyVectorStore,
    )
