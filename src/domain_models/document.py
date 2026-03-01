from collections.abc import AsyncGenerator
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain_models.chunk import SemanticChunk


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    title: str = Field(..., min_length=1, max_length=255, pattern=r"^[^<>;&]*$")
    file_path: str = Field(..., min_length=1, max_length=1024, pattern=r"^[^<>;&]*$")

    async def stream_chunks(self) -> AsyncGenerator[SemanticChunk, None]:
        """Abstract streaming iterator representing fetching large datasets."""
        # For demonstration purposes, this is a placeholder.
        # In a real implementation this would read line by line or block by block
        # from a file to avoid OOM.
        yield SemanticChunk(
            id=self.id,
            document_id=self.id,
            content="dummy"
        )
