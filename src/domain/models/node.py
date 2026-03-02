from uuid import UUID

from pydantic import Field

from src.domain.models.base import MutableBaseDomainModel


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
