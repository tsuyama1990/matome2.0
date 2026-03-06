from typing import Any, TypeVar

from src.domain.models.base import BaseDomainModel, MutableBaseDomainModel

TBase = TypeVar("TBase", bound=BaseDomainModel)
TMutable = TypeVar("TMutable", bound=MutableBaseDomainModel)


class DomainModelFactory:
    """Factory to create domain objects, supporting mutable or immutable variations."""

    @staticmethod
    def create_immutable(model_class: type[TBase], **kwargs: Any) -> TBase:
        return model_class(**kwargs)

    @staticmethod
    def create_mutable(model_class: type[TMutable], **kwargs: Any) -> TMutable:
        return model_class(**kwargs)
