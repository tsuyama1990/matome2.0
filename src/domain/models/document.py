from typing import Any
from uuid import UUID

from pydantic import Field

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
