import zlib
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SemanticChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    document_id: UUID
    content: str = Field(..., min_length=1, max_length=100_000)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    def compress_content(self) -> bytes:
        """Compress large text data for efficient storage."""
        return zlib.compress(self.content.encode("utf-8"))

    def decompress_content(self, compressed_data: bytes) -> str:
        """Decompress stored text data."""
        return zlib.decompress(compressed_data).decode("utf-8")
