import pytest

from src.core.exceptions import (
    InvalidChunkStateError,
    LLMProviderError,
    MatomeAppError,
    NodeNotFoundError,
)


def test_matome_app_exception() -> None:
    msg = "Base app error"
    with pytest.raises(MatomeAppError, match=msg):
        raise MatomeAppError(msg)


def test_node_not_found_error() -> None:
    msg = "Knowledge node with ID 123 was not found."
    with pytest.raises(NodeNotFoundError, match=msg):
        raise NodeNotFoundError("123")


def test_invalid_chunk_state_error() -> None:
    msg = "Chunk 456 is in an invalid state: state."
    with pytest.raises(InvalidChunkStateError, match=msg):
        raise InvalidChunkStateError("456", "state")


def test_llm_provider_error() -> None:
    msg = "LLM Provider AWS encountered an error: detail."
    with pytest.raises(LLMProviderError, match=msg):
        raise LLMProviderError("AWS", "detail")
