from uuid import UUID

from pydantic import Field

from src.domain.models.base import BaseDomainModel, MutableBaseDomainModel


class ConceptNode(MutableBaseDomainModel):
    """Hierarchical knowledge concept node."""

    node_id: UUID
    parent_id: UUID | None = None
    title: str
    summary: str = Field(..., description="High-density summary via Chain of Density")
    level: int = Field(..., ge=0)
    is_unlocked: bool = Field(default=False)
    chunk_references: list[UUID] = Field(default_factory=list)

    def unlock(self) -> None:
        """Unlocks the concept node for user access."""
        self.is_unlocked = True


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
