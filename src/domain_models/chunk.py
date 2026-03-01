from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SemanticChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    document_id: UUID
    content: str = Field(..., min_length=1)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
