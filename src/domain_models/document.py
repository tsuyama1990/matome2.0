from collections.abc import AsyncGenerator

from pydantic import UUID4, BaseModel, ConfigDict, Field

from src.domain_models.chunk import SemanticChunk


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID4
    title: str = Field(..., min_length=1, max_length=255, pattern=r"^[^<>;&]*$")
    file_path: str = Field(..., min_length=1, max_length=1024, pattern=r"^[^<>;&]*$")

    async def stream_chunks(self, block_size: int = 1024 * 64) -> AsyncGenerator[SemanticChunk, None]:
        """Streams document content directly from file without loading fully into memory."""
        import uuid

        import aiofiles
        import anyio

        path = anyio.Path(self.file_path)
        if not await path.exists():
            msg = f"Document path not found: {self.file_path}"
            raise FileNotFoundError(msg)

        async with aiofiles.open(self.file_path, encoding="utf-8") as f:
            while True:
                chunk_data = await f.read(block_size)
                if not chunk_data:
                    break

                chunk = SemanticChunk(
                    id=uuid.uuid4(),
                    document_id=self.id,
                    content=chunk_data
                )
                chunk.metadata["_compressed"] = chunk.compress_content().hex()
                yield chunk
