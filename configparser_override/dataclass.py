import ast
import configparser
import dataclasses
import logging
from types import UnionType
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from configparser_override.exceptions import ConversionError, LiteralEvalMiscast
from configparser_override.types import _dataclass

logger = logging.getLogger(__name__)


def _is_optional_type(type_hint: Any) -> bool:
    """
    Checks if a type hint is Optional.
    """
    return get_origin(type_hint) in [Union, UnionType] and type(None) in get_args(
        type_hint
    )


class ConfigConverter:
    def __init__(
        self,
        config: configparser.ConfigParser,
        boolean_states: Optional[Mapping[str, bool]] = None,
    ) -> None:
        self.config = config
        if boolean_states:
            self.boolean_states = boolean_states
        else:
            self.boolean_states = self.config.BOOLEAN_STATES

    def config_to_dict(self) -> dict[str, dict[str, str]]:
        config_dict: dict[str, dict[str, str]] = {}
        for sect in self.config.sections():
            # If missing add nested section
            if sect not in config_dict:
                config_dict[sect] = {}
            for opt in self.config.options(sect):
                config_dict[sect][opt] = self.config.get(section=sect, option=opt)
        # If missing add default nested section
        if self.config.default_section not in config_dict:
            config_dict[self.config.default_section] = {}
        for opt in self.config.defaults():
            config_dict[self.config.default_section][opt] = self.config.get(
                section=self.config.default_section, option=opt
            )
        return config_dict

    def config_to_dataclass(self, dataclass: _dataclass) -> _dataclass:
        config_dict = self.config_to_dict()
        return self._dict_to_dataclass(
            input_dict=config_dict,
            dataclass=dataclass,
        )

    def _dict_to_dataclass(self, input_dict: dict, dataclass: _dataclass) -> _dataclass:
        type_hints = get_type_hints(dataclass)

        _dict_with_types: dict[str, Any] = {}
        if not dataclasses.is_dataclass(dataclass):
            raise ValueError(f"object {dataclass} is not a Dataclass")
        for field in dataclasses.fields(dataclass):
            field_name = field.name
            field_type = type_hints[field_name]
            if field_name in input_dict:
                _dict_with_types[field_name] = self._cast_value(
                    value=input_dict[field_name],
                    type_hint=field_type,
                )
            elif not _is_optional_type(field_type):
                raise ValueError(f"Missing field: {field_name}")
        return dataclass(**_dict_with_types)

    def _cast_value(self, value: Any, type_hint: Any) -> Any:
        """
        Casts a value to a given type hint.
        """
        if dataclasses.is_dataclass(type_hint):
            return self._dict_to_dataclass(value, type_hint)  # type: ignore[type-var]
        if type_hint is Any:
            return value
        if type_hint in [int, float, str]:
            return type_hint(value)
        if type_hint is bytes:
            return str(value).encode()
        if type_hint is bool:
            return self._cast_bool(value)
        _origin = get_origin(type_hint)
        if _origin in [list, List]:
            return self._cast_list(value, type_hint)
        if _origin in [dict, Dict]:
            return self._cast_dict(value, type_hint)
        if _origin in (Optional, Union, UnionType):
            return self._cast_union(value, type_hint)
        if type_hint is type(None):
            return None
        raise ValueError(f"Unsupported type: {type_hint}")

    def _cast_bool(self, value: Any) -> bool:
        """
        Casts a value to a boolean.
        """
        if str(value).lower() in self.boolean_states:
            return self.boolean_states[str(value).lower()]
        else:
            raise ValueError(f"{value=} not in possible {self.boolean_states=}")

    def _cast_list(self, value: Any, type_hint: Any) -> list:
        """
        Casts a value to a list of a specific type.
        """
        _evaluated_option = ast.literal_eval(value) if isinstance(value, str) else value
        if isinstance(_evaluated_option, list):
            _types = get_args(type_hint)
            for typ in _types:
                try:
                    return [self._cast_value(item, typ) for item in _evaluated_option]
                except Exception as e:
                    logger.debug(f"Faild to cast {value=} into {typ=}, error: {e}")
                    continue
            raise ConversionError(
                f"Not possible to cast {value} into a list of {_types}"
            )
        raise LiteralEvalMiscast(
            f"{value} casted as {type(_evaluated_option)} expected {type_hint}"
        )

    def _cast_dict(self, value: Any, type_hint: Any) -> dict:
        """
        Casts a value to a dict of specific key and value types.
        """
        _evaluated_option = ast.literal_eval(value) if isinstance(value, str) else value
        if isinstance(_evaluated_option, dict):
            k_typ, v_typ = get_args(type_hint)
            try:
                return {
                    self._cast_value(k, k_typ): self._cast_value(v, v_typ)
                    for k, v in _evaluated_option.items()
                }
            except Exception as e:
                logger.debug(
                    f"Faild to cast {value=} into {k_typ=}, {v_typ=}, error: {e}"
                )
                raise ConversionError(
                    f"Not possible to cast {value} into a dict of keys of type {k_typ}, and values of type {v_typ}, Error: {e}"
                ) from e
        raise LiteralEvalMiscast(
            f"{value} casted as {type(_evaluated_option)} expected {type_hint}"
        )

    def _cast_union(self, value: Any, type_hint: Any) -> Any:
        """
        Casts a value to a union type.
        """
        for typ in get_args(type_hint):
            try:
                return self._cast_value(value, typ)
            except Exception as e:
                logger.debug(f"Faild to cast {value=} into {typ=}, error: {e}")
                continue
        raise ConversionError(f"Not possible to cast {value} into type {type_hint}")
