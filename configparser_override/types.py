from typing import Protocol


class _optionxform_fn(Protocol):
    def __call__(self, optionstr: str) -> str: ...  # pragma: no cover
