from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MockConceptNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: UUID
    parent_id: UUID | None = None
    title: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    level: int = Field(..., ge=0)
    is_unlocked: bool = Field(default=False)
    chunk_references: list[UUID] = Field(default_factory=list)

    def unlock(self) -> None:
        self.is_unlocked = True


class MockDocumentChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: UUID
    document_id: UUID
    text: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MockAnalysisAxis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    dimensions: list[str] = Field(..., min_length=1)


class MockPivotBoard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    board_id: UUID
    original_document_id: UUID
    axis: MockAnalysisAxis
    clusters: dict[str, list[MockConceptNode]] = Field(default_factory=dict)
