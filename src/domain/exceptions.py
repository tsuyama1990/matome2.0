class ConfigurationError(Exception):
    """Raised when an application component is incorrectly configured."""

    def __init__(self, message: str, config_key: str | None = None) -> None:
        """Initialize with an optional configuration key."""
        super().__init__(message)
        self.config_key = config_key


class DocumentProcessingError(Exception):
    """Raised when there is an error processing a document."""

    def __init__(self, message: str, document_id: str | None = None) -> None:
        """Initialize with an optional document ID context."""
        super().__init__(message)
        self.document_id = document_id
