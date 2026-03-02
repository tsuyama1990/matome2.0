from uuid import UUID

from pydantic import Field

from src.domain.models.base import BaseDomainModel
from src.domain.models.node import ConceptNode


class AnalysisAxis(BaseDomainModel):
    """Dimension used for Pivot KJ restructuring."""

    name: str = Field(..., description="e.g., SWOT, Timeline, Actor-State")
    dimensions: list[str] = Field(..., description="Categories within the axis")


class PivotBoard(BaseDomainModel):
    """Multi-dimensional reconstructed knowledge layout."""

    board_id: UUID
    original_document_id: UUID
    axis: AnalysisAxis
    clusters: dict[str, list[ConceptNode]] = Field(default_factory=dict)
