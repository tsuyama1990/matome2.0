from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from pathlib import Path


class IFileStorage(ABC):
    """Abstract interface for raw file storage operations."""

    @abstractmethod
    async def save_upload_stream(self, filename: str, stream: AsyncGenerator[bytes, None]) -> Path:
        """Saves a stream of bytes to a file, returning its path."""

    @abstractmethod
    async def read_file_stream(self, path: Path) -> AsyncGenerator[bytes, None]:
        """Reads a file yielding bytes as a stream."""
