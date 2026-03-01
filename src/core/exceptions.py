class MatomeAppError(Exception):
    """Base exception class for all Matome application errors."""


class NodeNotFoundError(MatomeAppError):
    """Raised when a KnowledgeNode cannot be found by its ID."""


class InvalidChunkStateError(MatomeAppError):
    """Raised when a SemanticChunk is in an invalid state for an operation."""


class LLMProviderError(MatomeAppError):
    """Raised when an external LLM provider API call fails."""
