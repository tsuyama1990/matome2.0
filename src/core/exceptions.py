class MatomeAppError(Exception):
    """Base exception class for all Matome application errors."""


class NodeNotFoundError(MatomeAppError):
    """Raised when a KnowledgeNode cannot be found by its ID."""

    message_template = "Knowledge node with ID {node_id} was not found."

    def __init__(self, node_id: str) -> None:
        super().__init__(self.message_template.format(node_id=node_id))


class InvalidChunkStateError(MatomeAppError):
    """Raised when a SemanticChunk is in an invalid state for an operation."""

    message_template = "Chunk {chunk_id} is in an invalid state: {reason}."

    def __init__(self, chunk_id: str, reason: str) -> None:
        super().__init__(self.message_template.format(chunk_id=chunk_id, reason=reason))


class LLMProviderError(MatomeAppError):
    """Raised when an external LLM provider API call fails."""

    message_template = "LLM Provider {provider_name} encountered an error: {detail}."

    def __init__(self, provider_name: str, detail: str) -> None:
        super().__init__(self.message_template.format(provider_name=provider_name, detail=detail))
