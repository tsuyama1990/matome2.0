from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict, Field


class InteractionState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID4
    document_id: UUID4
    locked_nodes: list[UUID4] = Field(default_factory=list)
    reviewed_nodes: list[UUID4] = Field(default_factory=list)
    active_question: str | None = None
    next_review_date: datetime | None = None
