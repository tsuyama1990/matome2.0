class MatomeAppError(Exception):
    """
    Base exception for all domain-specific errors in matome2-0.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ResourceNotFoundError(MatomeAppError):
    """
    Raised when a requested resource (e.g., Document, Chunk, Node) is not found.
    """


class ValidationDomainError(MatomeAppError):
    """
    Raised when domain-specific constraints are violated
    (independent of Pydantic structural validation).
    """
