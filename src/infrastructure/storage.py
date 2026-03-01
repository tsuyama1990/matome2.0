import codecs
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import aiofiles

from src.domain.ports.storage import IFileStorage


class LocalStorage(IFileStorage):
    """Concrete implementation for Local File Storage."""

    def __init__(
        self, base_dir: Path, create_dir: bool = True, path_class: type[Path] = Path
    ) -> None:
        self.path_class = path_class
        # Attempt to wrap the base_dir in the path_class if it's strictly a string/path
        self.base_dir = (
            self.path_class(base_dir) if not isinstance(base_dir, self.path_class) else base_dir
        )
        if create_dir:
            self.base_dir.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        """Explicitly creates the base directory if it doesn't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def exists(self, path: Path) -> bool:
        return path.exists()

    def get_metadata(self, path: Path) -> dict[str, Any]:
        stat = path.stat()
        return {"size": stat.st_size, "modified": stat.st_mtime}

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

        temp_path = safe_path.with_suffix(".tmp")

        def _check_size(w: int, maximum: int) -> None:
            if w > maximum:
                err_msg = f"File size exceeds maximum allowed of {maximum} bytes"
                raise ValueError(err_msg)

        try:
            written = 0
            with temp_path.open("wb") as f:
                async for chunk in stream:
                    written += len(chunk)
                    _check_size(written, max_size_bytes)
                    f.write(chunk)
        except Exception:
            # Clean up partial temp file in case of any failure
            if temp_path.exists():
                temp_path.unlink()
            raise
        else:
            # Atomic rename after successfully downloading stream
            temp_path.replace(safe_path)
            return Path(safe_path)  # Cast back to standard Path to satisfy return type

    def read_file_stream(self, path: Path) -> Generator[bytes, None, None]:
        """Reads a file yielding bytes as a stream."""
        if not path.is_absolute() or not path.resolve().is_relative_to(self.base_dir.resolve()):
            err_msg = "Path traversal attempt"
            raise ValueError(err_msg)

        with path.open("rb") as f:
            while chunk := f.read(1024 * 1024):  # 1MB chunks
                yield chunk

    async def read_file_stream_async(self, path: Path) -> AsyncGenerator[str, None]:
        """Reads a file asynchronously, yielding safely decoded text chunks."""
        from anyio import Path as AnyioPath

        anyio_p = AnyioPath(path)
        anyio_base = AnyioPath(self.base_dir)

        try:
            resolved_p = await anyio_p.resolve()
            resolved_base = await anyio_base.resolve()
            is_safe = path.is_absolute() and resolved_p.is_relative_to(resolved_base)
        except Exception:
            is_safe = False

        if not is_safe:
            err_msg = "Path traversal attempt"
            raise ValueError(err_msg)

        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

        async with aiofiles.open(path, "rb") as f:
            while True:
                chunk = await f.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    # Finalize decoding
                    final_text = decoder.decode(b"", final=True)
                    if final_text:
                        yield final_text
                    break

                text_chunk = decoder.decode(chunk, final=False)
                if text_chunk:
                    yield text_chunk
