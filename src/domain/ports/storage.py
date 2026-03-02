from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Generator
from typing import Any


class IFileStorage(ABC):
    """Abstract interface for raw file storage operations.

    Implementations must define explicit error handling protocols for IO access errors
    and ideally incorporate retry logic when interfacing with unstable remote storage providers
    (like S3 or GCS) to mitigate transient faults.
    """

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Checks if a file exists.

        Args:
            path (str): Path to check. Must be explicitly validated using operations
                        like `Path.relative_to(base_dir)` to guarantee it stays strictly
                        within the pre-configured storage bounds, rejecting directory
                        traversal attacks (e.g., paths containing `../`).

        Returns:
            bool: True if it exists safely, False otherwise.
        """

    @abstractmethod
    def get_metadata(self, path: str) -> dict[str, Any]:
        """Gets metadata for a file.

        Args:
            path (str): Path to the file.
        Returns:
            dict: File metadata.
        """

    @abstractmethod
    async def save_upload_stream(
        self,
        filename: str,
        stream: AsyncGenerator[bytes, None],
        max_size_bytes: int = 10 * 1024 * 1024,
    ) -> str:
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
    def read_file_stream(self, path: str) -> Generator[bytes, None, None]:
        """Reads a file yielding bytes as a stream.

        Args:
            path (str): The path to the file.

        Raises:
            FileNotFoundError: If the requested path does not exist.
            ValueError: If the path implies a path traversal attack outside bounds.
        """

    @abstractmethod
    def read_file_stream_async(
        self, path: str, encoding: str = "utf-8"
    ) -> AsyncGenerator[str, None]:
        """Reads a file asynchronously, yielding safely decoded text chunks.

        Args:
            path (str): The path to the file.
            encoding (str): Text encoding.

        Raises:
            FileNotFoundError: If the requested path does not exist.
            ValueError: If the path implies a path traversal attack outside bounds.
        """
