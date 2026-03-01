
from pydantic import UUID4, BaseModel, ConfigDict, Field, model_validator


class KnowledgeNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID4
    level: int = Field(ge=0)
    title: str = Field(..., min_length=1, max_length=512, pattern=r"^[^<>;&]*$")
    dense_summary: str = Field(..., min_length=1, max_length=2048)
    children: list[UUID4] = Field(default_factory=list)
    source_chunks: list[UUID4] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_cyclic_dependency(self) -> "KnowledgeNode":
        if self.id in self.children:
            msg = "Node cannot be its own child"
            raise ValueError(msg)
        return self
