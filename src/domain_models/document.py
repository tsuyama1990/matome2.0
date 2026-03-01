from collections.abc import AsyncGenerator
from pathlib import Path

from pydantic import UUID4, BaseModel, ConfigDict, Field

from src.domain_models.chunk import SemanticChunk


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID4
    title: str = Field(..., min_length=1, max_length=255, pattern=r"^[^<>;&]*$")
    file_path: str = Field(..., min_length=1, max_length=1024, pattern=r"^[^<>;&]*$")

    def _validate_path_security(self, allowed_dir: str | Path) -> None:
        """Ensures the file path is safe and does not traverse outside allowed directories."""
        from pathlib import Path

        allowed_path = Path(allowed_dir).resolve()
        resolved_path = Path(self.file_path).resolve()

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

        self._validate_path_security(allowed_dir)

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
                        yield chunk
                        buffer = []
                        current_size = 0

                    buffer.append(line)
                    current_size += line_len

                if buffer:
                    chunk_data = "".join(buffer)
                    chunk = SemanticChunk(id=uuid.uuid4(), document_id=self.id, content=chunk_data)
                    yield chunk

        except OSError as e:
            msg = f"Failed to read document: {e}"
            raise OSError(msg) from e
