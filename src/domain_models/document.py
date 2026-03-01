from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    title: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1)
