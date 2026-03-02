from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MockConceptNode(BaseModel):
    node_id: UUID
    parent_id: UUID | None = None
    title: str
    summary: str
    level: int
    is_unlocked: bool = False
    chunk_references: list[UUID] = Field(default_factory=list)

    def unlock(self) -> None:
        self.is_unlocked = True

class MockDocumentChunk(BaseModel):
    chunk_id: UUID
    document_id: UUID
    text: str
    metadata: dict[str, Any]

class MockAnalysisAxis(BaseModel):
    name: str
    dimensions: list[str]

class MockPivotBoard(BaseModel):
    board_id: UUID
    original_document_id: UUID
    axis: MockAnalysisAxis
    clusters: dict[str, list[MockConceptNode]]
