from collections.abc import AsyncGenerator
from pathlib import Path

from pydantic import UUID4, BaseModel, ConfigDict, Field

from src.domain_models.chunk import SemanticChunk


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0.0", frozen=True)
    id: UUID4
    title: str = Field(..., min_length=1, max_length=255, pattern=r"^[^<>;&]*$")
    file_path: str = Field(..., min_length=1, max_length=1024, pattern=r"^[^<>;&]*$")

    async def _validate_path_security_async(self, allowed_dir: str | Path) -> None:
        """Ensures the file path is safe and does not traverse outside allowed directories asynchronously."""
        import asyncio
        from pathlib import Path

        def _resolve_paths() -> tuple[Path, Path]:
            return Path(allowed_dir).resolve(), Path(self.file_path).resolve()

        # Offload synchronous path resolution which hits the disk to a thread pool
        allowed_path, resolved_path = await asyncio.to_thread(_resolve_paths)

        if ".." in Path(self.file_path).parts:
            msg = "Directory traversal detected in file_path"
            raise ValueError(msg)

        try:
            resolved_path.relative_to(allowed_path)
        except ValueError:
            msg = f"File path must be within {allowed_path}"
            raise ValueError(msg) from None

    async def stream_chunks(
        self, allowed_dir: str | Path, block_size: int = 10_000
    ) -> AsyncGenerator[SemanticChunk, None]:
        """Streams document content directly from file using aiofiles with buffered generator."""
        import uuid

        import aiofiles
        import anyio

        await self._validate_path_security_async(allowed_dir)

        path = anyio.Path(self.file_path)
        if not await path.exists():
            msg = f"Document path not found: {self.file_path}"
            raise FileNotFoundError(msg)

        import codecs

        try:
            # Open binary for efficient block-level reading without slow line-by-line parsing
            async with aiofiles.open(self.file_path, "rb") as f:
                # Stateful incremental decoder correctly handles multi-byte characters split across chunk boundaries
                decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
                while True:
                    chunk_bytes = await f.read(block_size)
                    if not chunk_bytes:
                        # Flush the final decoded bytes
                        final_data = decoder.decode(b"", final=True)
                        if final_data.strip():
                            yield SemanticChunk(
                                id=uuid.uuid4(), document_id=self.id, content=final_data
                            )
                        break

                    try:
                        chunk_data = decoder.decode(chunk_bytes, final=False)
                    except UnicodeError as ue:
                        msg = "Failed to decode chunk"
                        enc = "utf-8"
                        raise UnicodeDecodeError(enc, chunk_bytes, 0, len(chunk_bytes), msg) from ue

                    if chunk_data.strip():
                        yield SemanticChunk(
                            id=uuid.uuid4(), document_id=self.id, content=chunk_data
                        )

        except OSError as e:
            msg = f"Failed to read document: {e}"
            raise OSError(msg) from e
