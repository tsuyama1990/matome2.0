from pydantic import UUID4, BaseModel, ConfigDict, Field


class PivotGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID4
    source_document_ids: list[UUID4] = Field(default_factory=list)
    analytical_axis: str = Field(..., min_length=1, max_length=255)
    clusters: dict[str, list[UUID4]] = Field(default_factory=dict)
