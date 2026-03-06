import typing
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class DomainEventDispatcher:
    """Placeholder for domain event dispatching logic."""

    @staticmethod
    def dispatch(event: Any) -> None:
        pass


class BaseDomainModel(BaseModel):
    """Base domain model enforcing strict validation rules.

    This class should be inherited by all Pydantic models in the domain layer to ensure consistency.
    It strictly forbids extra attributes that are not defined in the schema to prevent silent
    data errors.

    Crucially, it makes models `frozen=True` (immutable) after creation to prevent side effects
    during passing between different application layers. This immutability guarantee ensures that
    domain objects remain thread-safe and predictable across asynchronous tasks. If you need to
    update a model after it's created, you MUST use the `update(key=value)` method. This method
    internally wraps `model_copy(update={...})`, safely creating a new, isolated instance with
    the modified fields without mutating the original object's internal state.
    """

    schema_version: int = Field(
        default=1, description="Schema version for data migration and backward compatibility."
    )
    _domain_events: list[Any] = PrivateAttr(default_factory=list)

    def add_domain_event(self, event: Any) -> None:
        self._domain_events.append(event)

    def clear_domain_events(self) -> None:
        self._domain_events.clear()

    @property
    def domain_events(self) -> list[Any]:
        return self._domain_events.copy()

    model_config = ConfigDict(extra="forbid", frozen=True)

    def update(self, **kwargs: typing.Any) -> typing.Self:
        """Creates an updated copy of the model, maintaining immutability."""
        return self.model_copy(update=kwargs)


class MutableBaseDomainModel(BaseModel):
    """Mutable base domain model enforcing strict validation rules without freezing fields.

    Use this base class when domain objects require modification after instantiation.
    """

    schema_version: int = Field(
        default=1, description="Schema version for data migration and backward compatibility."
    )
    _domain_events: list[Any] = PrivateAttr(default_factory=list)

    def add_domain_event(self, event: Any) -> None:
        self._domain_events.append(event)

    def clear_domain_events(self) -> None:
        self._domain_events.clear()

    @property
    def domain_events(self) -> list[Any]:
        return self._domain_events.copy()

    model_config = ConfigDict(extra="forbid")
