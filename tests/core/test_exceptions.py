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
    msg = "Node ID not found"
    with pytest.raises(NodeNotFoundError, match=msg):
        raise NodeNotFoundError(msg)

def test_invalid_chunk_state_error() -> None:
    msg = "Chunk is in invalid state"
    with pytest.raises(InvalidChunkStateError, match=msg):
        raise InvalidChunkStateError(msg)

def test_llm_provider_error() -> None:
    msg = "LLM provider failed to generate completion"
    with pytest.raises(LLMProviderError, match=msg):
        raise LLMProviderError(msg)
