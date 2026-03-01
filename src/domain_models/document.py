from collections.abc import AsyncGenerator

from pydantic import UUID4, BaseModel, ConfigDict, Field

from src.domain_models.chunk import SemanticChunk


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID4
    title: str = Field(..., min_length=1, max_length=255, pattern=r"^[^<>;&]*$")
    file_path: str = Field(..., min_length=1, max_length=1024, pattern=r"^[^<>;&]*$")

    def _validate_path_security(self) -> None:
        """Ensures the file path is safe and does not traverse outside allowed directories."""
        from pathlib import Path

        from src.core.config import AppSettings

        config = AppSettings(_env_file=".env", _env_file_encoding="utf-8")  # type: ignore[call-arg]
        allowed_dir = config.ALLOWED_DOCUMENT_DIR.resolve()
        resolved_path = Path(self.file_path).resolve()

        if ".." in Path(self.file_path).parts:
            msg = "Directory traversal detected in file_path"
            raise ValueError(msg)

        if not str(resolved_path).startswith(str(allowed_dir)):
            msg = f"File path must be within {allowed_dir}"
            raise ValueError(msg)

    async def stream_chunks(self, block_size: int = 10_000) -> AsyncGenerator[SemanticChunk, None]:
        """Streams document content directly from file using aiofiles with buffered generator."""
        import uuid

        import aiofiles
        import anyio

        self._validate_path_security()

        path = anyio.Path(self.file_path)
        if not await path.exists():
            msg = f"Document path not found: {self.file_path}"
            raise FileNotFoundError(msg)

        try:
            async with aiofiles.open(self.file_path, encoding="utf-8") as f:
                buffer: list[str] = []
                current_size = 0

                async for line in f:
                    line_len = len(line)
                    if current_size + line_len > block_size and buffer:
                        chunk_data = "".join(buffer)
                        chunk = SemanticChunk(
                            id=uuid.uuid4(), document_id=self.id, content=chunk_data
                        )
                        chunk.metadata["_compressed"] = chunk.compress_content().hex()
                        yield chunk
                        buffer = []
                        current_size = 0

                    buffer.append(line)
                    current_size += line_len

                if buffer:
                    chunk_data = "".join(buffer)
                    chunk = SemanticChunk(id=uuid.uuid4(), document_id=self.id, content=chunk_data)
                    chunk.metadata["_compressed"] = chunk.compress_content().hex()
                    yield chunk

        except OSError as e:
            msg = f"Failed to read document: {e}"
            raise OSError(msg) from e
