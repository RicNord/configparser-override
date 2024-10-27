from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

    Dataclass = TypeVar("Dataclass", bound=DataclassInstance)


class _optionxform_fn(Protocol):
    def __call__(self, optionstr: str) -> str: ...  # pragma: no cover


class SecretType(ABC):
    _secret: Any

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.get_secret_value() == other.get_secret_value()
        )

    def __hash__(self) -> int:
        return hash(self.get_secret_value())

    def __str__(self) -> str:
        return "**********" if self.get_secret_value() else ""

    def __len__(self) -> int:
        return len(self._secret)

    @abstractmethod
    def get_secret_value(self) -> Any:
        pass


class SecretStr(SecretType):
    _secret: str

    def __init__(self, value: str):
        self._secret = value

    def __repr__(self) -> str:
        return f'SecretStr(value="{self}")'

    def get_secret_value(self) -> str:
        return self._secret


class SecretBytes(SecretType):
    _secret: bytes

    def __init__(self, value: bytes):
        self._secret = value

    def __repr__(self) -> str:
        return f'SecretBytes(value=b"{self}")'

    def get_secret_value(self) -> bytes:
        return self._secret
