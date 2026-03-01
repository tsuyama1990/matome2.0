from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Generator
from pathlib import Path


class IFileStorage(ABC):
    """Abstract interface for raw file storage operations."""

    @abstractmethod
    async def save_upload_stream(
        self,
        filename: str,
        stream: AsyncGenerator[bytes, None],
        max_size_bytes: int = 10 * 1024 * 1024,
    ) -> Path:
        """Saves a stream of bytes to a file, returning its path.

        Args:
            filename (str): The name to save the file under.
            stream (AsyncGenerator[bytes, None]): An asynchronous generator yielding file chunks.
            max_size_bytes (int): Maximum allowed file size before aborting, preventing OOM / disk full.

        Raises:
            ValueError: If the total size exceeds the `max_size_bytes` or if path traversal is attempted.
                        In either case, incomplete partial files should be cleaned up.
            IOError: If an error occurs writing to the underlying disk or blob storage.
        """

    @abstractmethod
    def read_file_stream(self, path: Path) -> Generator[bytes, None, None]:
        """Reads a file yielding bytes as a stream.

        Args:
            path (Path): The path to the file.

        Raises:
            FileNotFoundError: If the requested path does not exist.
            ValueError: If the path implies a path traversal attack outside bounds.
        """

    @abstractmethod
    def read_file_stream_async(self, path: Path) -> AsyncGenerator[str, None]:
        """Reads a file asynchronously, yielding safely decoded text chunks.

        Args:
            path (Path): The path to the file.

        Raises:
            FileNotFoundError: If the requested path does not exist.
            ValueError: If the path implies a path traversal attack outside bounds.
        """
