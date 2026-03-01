from pydantic import BaseModel, ConfigDict


class BaseDomainModel(BaseModel):
    """Base domain model enforcing strict validation rules."""

    model_config = ConfigDict(extra="forbid", frozen=True)
