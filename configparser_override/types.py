from typing import Any, Protocol, TypeVar


class _optionxform_fn(Protocol):
    def __call__(self, optionstr: str) -> str: ...  # pragma: no cover


class _CallableProtocol(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...  # pragma: no cover


_dataclass = TypeVar("_dataclass", bound=_CallableProtocol)
