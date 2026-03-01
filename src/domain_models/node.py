from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class KnowledgeNode(BaseModel):
    """
    Building block of the RAPTOR hierarchical tree.
    """

    id: UUID
    level: int = Field(ge=0)
    title: str = Field(min_length=1)
    dense_summary: str = Field(max_length=2000)
    children: list[UUID] = Field(default_factory=list)
    source_chunks: list[UUID] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_no_self_child(self) -> "KnowledgeNode":
        if self.id in self.children:
            msg = "A node cannot be its own child."
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_no_empty_title(self) -> "KnowledgeNode":
        if not self.title.strip():
            msg = "title must not be whitespace only"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_summary_not_empty(self) -> "KnowledgeNode":
        if not self.dense_summary.strip():
            msg = "dense_summary must not be whitespace only"
            raise ValueError(msg)
        return self
