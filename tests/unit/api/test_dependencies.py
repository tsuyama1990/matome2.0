import pytest

from src.api.dependencies import (
    MockLLMProvider,
    MockVectorStore,
    get_llm_provider,
    get_vector_store,
)


@pytest.mark.asyncio
async def test_mock_llm_provider() -> None:
    provider = MockLLMProvider()
    res = await provider.generate_completion("test")
    assert res == "mock completion"


@pytest.mark.asyncio
async def test_mock_vector_store() -> None:
    store = MockVectorStore()
    assert await store.upsert_chunks([]) is True
    assert await store.search([0.1], 5) == []


@pytest.mark.asyncio
async def test_get_llm_provider() -> None:
    generator = get_llm_provider()
    provider = await generator.__anext__()
    assert isinstance(provider, MockLLMProvider)


@pytest.mark.asyncio
async def test_get_vector_store() -> None:
    generator = get_vector_store()
    store = await generator.__anext__()
    assert isinstance(store, MockVectorStore)
