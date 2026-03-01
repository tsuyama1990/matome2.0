from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceType(StrEnum):
    """Supported document source types."""

    PDF = "PDF"
    EPUB = "EPUB"
    MARKDOWN = "MARKDOWN"


class IngestionStatus(StrEnum):
    """Statuses for the document ingestion pipeline."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(BaseModel):
    """
    Represents an ingested file and acts as the aggregate root for a specific document.
    """

    id: UUID
    filename: str = Field(min_length=1)
    source_type: SourceType
    ingestion_status: IngestionStatus = IngestionStatus.PENDING
    root_node_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_filename_not_empty(self) -> "Document":
        if not self.filename.strip():
            msg = "filename must not be whitespace only"
            raise ValueError(msg)
        return self
