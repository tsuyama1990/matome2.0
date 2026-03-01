from collections.abc import AsyncGenerator, Generator
from pathlib import Path

from src.domain.ports.storage import IFileStorage


class LocalStorage(IFileStorage):
    """Concrete implementation for Local File Storage."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload_stream(
        self,
        filename: str,
        stream: AsyncGenerator[bytes, None],
        max_size_bytes: int = 10 * 1024 * 1024,
    ) -> Path:
        """Saves a stream of bytes to a file, returning its path."""
        safe_path = self.base_dir / filename
        if not safe_path.resolve().is_relative_to(self.base_dir.resolve()):
            err_msg = "Path traversal attempt"
            raise ValueError(err_msg)

        written = 0
        with safe_path.open("wb") as f:
            async for chunk in stream:
                written += len(chunk)
                if written > max_size_bytes:
                    err_msg = f"File size exceeds maximum allowed of {max_size_bytes} bytes"
                    raise ValueError(err_msg)
                f.write(chunk)
        return safe_path

    def read_file_stream(self, path: Path) -> Generator[bytes, None, None]:
        """Reads a file yielding bytes as a stream."""
        if not path.is_absolute() or not str(path).startswith(str(self.base_dir)):
            # Ensure the path is within the base_dir to avoid path traversal
            err_msg = "Path traversal attempt"
            raise ValueError(err_msg)

        with path.open("rb") as f:
            while chunk := f.read(1024 * 1024):  # 1MB chunks
                yield chunk
