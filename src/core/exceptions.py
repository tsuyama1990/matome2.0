from src.core.constants import (
    ERR_MSG_INVALID_CHUNK_STATE,
    ERR_MSG_LLM_PROVIDER_ERROR,
    ERR_MSG_NODE_NOT_FOUND,
)


class MatomeAppError(Exception):
    """Base exception class for all Matome application errors."""


class NodeNotFoundError(MatomeAppError):
    """Raised when a KnowledgeNode cannot be found by its ID."""

    def __init__(self, node_id: str) -> None:
        super().__init__(ERR_MSG_NODE_NOT_FOUND.format(node_id=node_id))


class InvalidChunkStateError(MatomeAppError):
    """Raised when a SemanticChunk is in an invalid state for an operation."""

    def __init__(self, chunk_id: str, reason: str) -> None:
        super().__init__(ERR_MSG_INVALID_CHUNK_STATE.format(chunk_id=chunk_id, reason=reason))


class LLMProviderError(MatomeAppError):
    """Raised when an external LLM provider API call fails."""

    def __init__(self, provider_name: str, detail: str) -> None:
        super().__init__(
            ERR_MSG_LLM_PROVIDER_ERROR.format(provider_name=provider_name, detail=detail)
        )
