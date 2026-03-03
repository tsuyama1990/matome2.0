from uuid import UUID

from pydantic import Field, model_validator

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

    @model_validator(mode="after")
    def validate_hierarchy(self) -> 'ConceptNode':
        if self.level == 0 and self.parent_id is not None:
            raise ValueError("Root nodes (level 0) cannot have a parent")
        if self.level > 0 and self.parent_id is None:
            raise ValueError("Child nodes (level > 0) must have a parent")
        return self

    def unlock(self) -> None:
        """Unlocks the concept node for user access."""
        self.is_unlocked = True
