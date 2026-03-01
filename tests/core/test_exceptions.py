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
    expected_msg = "Knowledge node with ID 123 was not found."
    node_id = "123"
    with pytest.raises(NodeNotFoundError, match=expected_msg):
        raise NodeNotFoundError(node_id)


def test_invalid_chunk_state_error() -> None:
    expected_msg = "Chunk 456 is in an invalid state: state."
    chunk_id = "456"
    with pytest.raises(InvalidChunkStateError, match=expected_msg):
        raise InvalidChunkStateError(chunk_id, "state")


def test_llm_provider_error() -> None:
    expected_msg = "LLM Provider AWS encountered an error: detail."
    provider = "AWS"
    with pytest.raises(LLMProviderError, match=expected_msg):
        raise LLMProviderError(provider, "detail")
