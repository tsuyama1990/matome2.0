from __future__ import annotations

import codecs
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import aiofiles

from src.domain.ports.storage import IFileStorage


class StorageFactory:
    """Factory to create and configure storage instances for multiple backends (Local, S3, GCS)."""

    @staticmethod
    def create_local_storage(
        base_dir: str | Path,
        max_upload_size: int,
        create_dir: bool = True,
        path_class: type[Path] = Path,
    ) -> IFileStorage:
        """Initializes and returns a LocalStorage instance."""
        return LocalStorage(
            base_dir=path_class(base_dir) if isinstance(base_dir, str) else base_dir,
            max_upload_size=max_upload_size,
            create_dir=create_dir,
            path_class=path_class,
        )

    @staticmethod
    def create_s3_storage(bucket_name: str) -> IFileStorage:
        """Initializes and returns an S3 storage instance (stub)."""
        raise NotImplementedError("S3 storage backend is not yet fully implemented.")

    @staticmethod
    def create_gcs_storage(bucket_name: str) -> IFileStorage:
        """Initializes and returns a GCS storage instance (stub)."""
        raise NotImplementedError("GCS storage backend is not yet fully implemented.")


class LocalStorage(IFileStorage):
    """Concrete implementation for Local File Storage."""

    def __init__(
        self,
        base_dir: Path,
        max_upload_size: int,
        create_dir: bool = True,
        path_class: type[Path] = Path,
    ) -> None:
        self.path_class = path_class
        self.max_upload_size = max_upload_size
        # Attempt to wrap the base_dir in the path_class if it's strictly a string/path
        self.base_dir = (
            self.path_class(base_dir) if not isinstance(base_dir, self.path_class) else base_dir
        )
        if not self.base_dir.is_absolute():
            self.base_dir = self.base_dir.resolve()

        if create_dir:
            self.base_dir.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        """Explicitly creates the base directory if it doesn't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def exists(self, path: str) -> bool:
        p = self.path_class(path)
        return p.exists()

    def get_metadata(self, path: str) -> dict[str, Any]:
        p = self.path_class(path)
        stat = p.stat()
        return {"size": stat.st_size, "modified": stat.st_mtime}

    async def save_upload_stream(
        self,
        filename: str,
        stream: AsyncGenerator[bytes, None],
        max_size_bytes: int | None = None,
    ) -> str:
        """Saves a stream of bytes to a file, returning its path."""
        if max_size_bytes is None:
            max_size_bytes = self.max_upload_size
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
            return str(safe_path)  # Return string to satisfy interface

    def read_file_stream(self, path: str) -> Generator[bytes, None, None]:
        """Reads a file yielding bytes as a stream."""
        p = self.path_class(path)
        if not p.is_absolute() or not p.resolve().is_relative_to(self.base_dir.resolve()):
            err_msg = "Path traversal attempt"
            raise ValueError(err_msg)

        with p.open("rb") as f:
            while chunk := f.read(1024 * 1024):  # 1MB chunks
                yield chunk

    async def read_file_stream_async(
        self, path: str, encoding: str = "utf-8"
    ) -> AsyncGenerator[str, None]:
        """Reads a file asynchronously, yielding safely decoded text chunks."""
        from anyio import Path as AnyioPath

        p = self.path_class(path)
        anyio_p = AnyioPath(p)
        anyio_base = AnyioPath(self.base_dir)

        try:
            resolved_p = await anyio_p.resolve()
            resolved_base = await anyio_base.resolve()
            is_safe = p.is_absolute() and resolved_p.is_relative_to(resolved_base)
        except Exception:
            is_safe = False

        if not is_safe:
            err_msg = "Path traversal attempt"
            raise ValueError(err_msg)

        decoder = codecs.getincrementaldecoder(encoding)(errors="replace")

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
