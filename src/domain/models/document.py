from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from src.domain.models.base import BaseDomainModel


class DocumentChunk(BaseDomainModel):
    """Semantic chunk extracted from a document."""

    chunk_id: UUID
    document_id: UUID
    text: str = Field(..., description="The semantic proposition text")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Extracted entities and tags"
    )
    embedding: list[float] | None = None

    @field_validator("embedding")
    @classmethod
    def validate_embedding(cls, v: list[float] | None) -> list[float] | None:
        if v is not None and len(v) == 0:
            raise ValueError("Embedding must not be empty if provided")
        return v
