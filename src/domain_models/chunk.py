from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SemanticChunk(BaseModel):
    """
    Represents the atomic unit of ingested information.
    """

    id: UUID
    content: str = Field(min_length=1)
    embedding: list[float] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_content_not_empty(self) -> "SemanticChunk":
        if not self.content.strip():
            msg = "content must not be empty or whitespace only"
            raise ValueError(msg)
        return self
