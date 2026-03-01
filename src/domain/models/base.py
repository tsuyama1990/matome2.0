from pydantic import BaseModel, ConfigDict


class BaseDomainModel(BaseModel):
    """Base domain model enforcing strict validation rules.

    This class should be inherited by all Pydantic models in the domain layer to ensure consistency.
    It strictly forbids extra attributes that are not defined in the schema to prevent silent
    data errors, and it makes models frozen (immutable) after creation to prevent side effects
    during passing between different application layers.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
