from pydantic import BaseModel, ConfigDict


class BaseDomainModel(BaseModel):
    """Base domain model enforcing strict validation rules.

    This class should be inherited by all Pydantic models in the domain layer to ensure consistency.
    It strictly forbids extra attributes that are not defined in the schema to prevent silent
    data errors.

    Crucially, it makes models `frozen=True` (immutable) after creation to prevent side effects
    during passing between different application layers. If you need to update a model after it's
    created, you MUST use the `model_copy(update={...})` method, which safely creates a new instance
    with the modified fields without mutating the original object's state.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class MutableBaseDomainModel(BaseModel):
    """Mutable base domain model enforcing strict validation rules without freezing fields.

    Use this base class when domain objects require modification after instantiation.
    """

    model_config = ConfigDict(extra="forbid")
