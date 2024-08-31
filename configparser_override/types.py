from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

    Dataclass = TypeVar("Dataclass", bound=DataclassInstance)


class _optionxform_fn(Protocol):
    def __call__(self, optionstr: str) -> str: ...  # pragma: no cover
