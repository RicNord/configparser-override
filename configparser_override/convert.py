from __future__ import annotations

import ast
import dataclasses
import logging
from pathlib import Path
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

if TYPE_CHECKING:
    import configparser

    from configparser_override.types import Dataclass

from configparser_override.exceptions import (
    ConversionError,
    ConversionIgnoreError,
    InvalidParametersError,
    LiteralEvalMiscast,
)
from configparser_override.types import SecretBytes, SecretStr

logger = logging.getLogger(__name__)


def _is_optional_type(type_hint: Any) -> bool:
    """
    Check if a given type hint is an optional type.
    """
    return get_origin(type_hint) in [Union, UnionType] and type(None) in get_args(
        type_hint
    )


def _is_optional_dataclass(type_hint: Any) -> bool:
    """
    Check if a given type hint is an optional dataclass.
    """
    if get_origin(type_hint) not in [Union, UnionType]:
        return False

    for arg in get_args(type_hint):
        if arg is type(None) or dataclasses.is_dataclass(arg):
            continue
        else:
            return False

    return True


def _field_has_default_value(field: dataclasses.Field) -> bool:
    """
    Check if a given dataclass field has a default value.
    """
    return (
        field.default_factory != dataclasses.MISSING
        or field.default != dataclasses.MISSING
    )


def _can_ignore_section(field: dataclasses.Field) -> bool:
    return _is_optional_dataclass(field.type) or _field_has_default_value(field)


def _can_ignore_conversion(field: dataclasses.Field) -> bool:
    return _is_optional_type(field.type) or _field_has_default_value(field)


class ConfigConverter:
    """
    A class to convert configuration data from a ConfigParser object to a dictionary
    or dataclass.

    :param config: The configuration parser object.
    :type config: configparser.ConfigParser
    :param boolean_states: Optional mapping of custom boolean states,
        defaults to None and uses the internal mapping of the ConfigParser object.
    :type boolean_states: Optional[Mapping[str, bool]], optional
    """

    def __init__(
        self,
        config: configparser.ConfigParser,
        boolean_states: Optional[Mapping[str, bool]] = None,
        include_sections: Optional[List[str]] = None,
        exclude_sections: Optional[List[str]] = None,
    ) -> None:
        self.config = config

        if include_sections is not None and exclude_sections is not None:
            raise InvalidParametersError(
                "Not allows to specify both include_sections and exclude_sections parameters at the same time"
            )
        self.include_sections = include_sections
        self.exclude_sections = exclude_sections

        if boolean_states:
            self.boolean_states = boolean_states
        else:
            self.boolean_states = self.config.BOOLEAN_STATES

    def to_dataclass(self, dataclass: Type[Dataclass]) -> Dataclass:
        """
        Convert the configuration data to a dataclass instance.

        :param dataclass: The dataclass type to convert the configuration data into.
        :type dataclass: Dataclass
        :return: An instance of the dataclass populated with the configuration data.
        :rtype: Dataclass

        **Examples:**

        .. code-block:: python

            >>> from dataclasses import dataclass

            >>> @dataclass
            ... class Section1:
            ...     key: str

            >>> @dataclass
            ... class ExampleConfig:
            ...     section1: Section1

            >>> config = configparser.ConfigParser()
            >>> config.read_string(\"\"\"
            ... [section1]
            ... key = value
            ... \"\"\")
            >>> converter = ConfigConverter(config)
            >>> config_as_dataclass = converter.to_dataclass(ExampleConfig)
            >>> assert config_as_dataclass.section1.key == "value" # True
        """
        for sect in dataclasses.fields(dataclass):
            if sect.name != self.config.default_section and not self.config.has_section(
                sect.name
            ):
                self.config.add_section(sect.name)

        config_dict = self._to_dict()
        return self._dict_to_dataclass(
            input_dict=config_dict,
            dataclass=dataclass,
        )

    def _to_dict(self) -> dict[str, dict[str, str]]:
        """
        Convert the configuration data to a nested dictionary.

        :return: The configuration data as a dictionary.
        :rtype: dict[str, dict[str, str]]

        **Examples:**

        .. code-block:: python

            >>> config = configparser.ConfigParser()
            >>> config.read_string(\"\"\"
            ... [section1]
            ... key1 = value1
            ... [section2]
            ... key2 = value2
            ... \"\"\")
            >>> converter = ConfigConverter(config)
            >>> config_dict = converter._to_dict()
            >>> config_dict['section1']['key1']
            'value1'
        """
        config_dict: dict[str, dict[str, str]] = {}
        for sect in self.config.sections():
            # Add nested sections
            config_dict[sect] = {}
            for opt in self.config.options(sect):
                config_dict[sect][opt] = self.config.get(section=sect, option=opt)
        # Add default nested section
        config_dict[self.config.default_section] = {}
        for opt in self.config.defaults():
            config_dict[self.config.default_section][opt] = self.config.get(
                section=self.config.default_section, option=opt
            )
        return config_dict

    def _dict_to_dataclass(
        self,
        input_dict: dict,
        dataclass: Type[Dataclass],
        nested_level: int = 0,
    ) -> Dataclass:
        type_hints = get_type_hints(dataclass)

        _dict_with_types: dict[str, Any] = {}
        for field in dataclasses.fields(dataclass):
            field_name = field.name
            field_type = type_hints[field_name]
            logger.debug(f"Initiate conversion of {field_name=} and {field_type=}")

            # Skip convertion of specified sections
            if nested_level == 0 and not self._parse_section(field_name):
                if _can_ignore_section(field):
                    logger.debug(f"Ignore conversion of section {field_name}")
                    continue
                else:
                    raise ConversionIgnoreError(
                        f"Can not skip {field_name=}, the field is not optional nor have a default or default_factory assignment."
                    )

            # Create dict with field names and casted values
            if field_name in input_dict:
                logger.debug(f"Initiate type cast of {field_name=} to {field_type=}")
                _dict_with_types[field_name] = self._cast_value(
                    value=input_dict[field_name],
                    type_hint=field_type,
                    nested_level=nested_level,
                )
            elif not _can_ignore_conversion(field):
                raise ConversionIgnoreError(
                    f"Config not found and not allowed to skip {field_name=}, the field is not optional nor have a default or default_factory assignment."
                )
        return dataclass(**_dict_with_types)

    def _parse_section(self, section: str) -> bool:
        is_not_included = (
            self.include_sections is not None and section not in self.include_sections
        )
        is_excluded = (
            self.exclude_sections is not None and section in self.exclude_sections
        )

        return not (is_not_included or is_excluded)

    def _cast_value(self, value: Any, type_hint: Any, nested_level: int = 0) -> Any:
        if dataclasses.is_dataclass(type_hint):
            logger.debug("Type hint is a Dataclass")
            _type_hint = type_hint if isinstance(type_hint, type) else type(type_hint)
            return self._dict_to_dataclass(
                input_dict=value, dataclass=_type_hint, nested_level=nested_level + 1
            )
        if type_hint is Any:
            return value
        if type_hint in [int, float, complex, str, Path, SecretStr]:
            return type_hint(value)
        if type_hint is bytes:
            return str(value).encode()
        if type_hint is SecretBytes:
            return SecretBytes(str(value).encode())
        if type_hint is bool:
            return self._cast_bool(value)
        _origin = get_origin(type_hint)
        if _origin in [list, List]:
            return self._cast_list(value, type_hint)
        if _origin in [dict, Dict]:
            return self._cast_dict(value, type_hint)
        if _origin in [set, Set]:
            return self._cast_set(value, type_hint)
        if _origin in [tuple, Tuple]:
            return self._cast_tuple(value, type_hint)
        if _origin in (Optional, Union, UnionType):
            return self._cast_union(value, type_hint)
        if type_hint is type(None):
            return None
        raise ValueError(f"Unsupported type: {type_hint}")

    def _cast_bool(self, value: Any) -> bool:
        if str(value).lower() in self.boolean_states:
            return self.boolean_states[str(value).lower()]
        else:
            raise ValueError(f"{value=} not in possible {self.boolean_states=}")

    def _cast_list(self, value: Any, type_hint: Any) -> list:
        _evaluated_option = ast.literal_eval(value) if isinstance(value, str) else value
        if isinstance(_evaluated_option, list):
            _types = get_args(type_hint)
            for typ in _types:
                try:
                    return [self._cast_value(item, typ) for item in _evaluated_option]
                except Exception as e:
                    logger.debug(f"Failed to cast {value=} into {typ=}, error: {e}")
                    continue
            raise ConversionError(
                f"Not possible to cast {value} into a list of {_types}"
            )
        raise LiteralEvalMiscast(
            f"{value} casted as {type(_evaluated_option)} expected {type_hint}"
        )

    def _cast_set(self, value: Any, type_hint: Any) -> set:
        _evaluated_option = ast.literal_eval(value) if isinstance(value, str) else value
        if isinstance(_evaluated_option, set):
            _types = get_args(type_hint)
            for typ in _types:
                try:
                    return {self._cast_value(item, typ) for item in _evaluated_option}
                except Exception as e:
                    logger.debug(f"Failed to cast {value=} into {typ=}, error: {e}")
                    continue
            raise ConversionError(
                f"Not possible to cast {value} into a set of {_types}"
            )
        raise LiteralEvalMiscast(
            f"{value} casted as {type(_evaluated_option)} expected {type_hint}"
        )

    def _cast_tuple(self, value: Any, type_hint: Any) -> tuple:
        _evaluated_option = ast.literal_eval(value) if isinstance(value, str) else value
        if isinstance(_evaluated_option, tuple):
            _types = get_args(type_hint)
            for typ in _types:
                try:
                    return tuple(
                        self._cast_value(item, typ) for item in _evaluated_option
                    )
                except Exception as e:
                    logger.debug(f"Failed to cast {value=} into {typ=}, error: {e}")
                    continue
            raise ConversionError(
                f"Not possible to cast {value} into a tuple of {_types}"
            )
        raise LiteralEvalMiscast(
            f"{value} casted as {type(_evaluated_option)} expected {type_hint}"
        )

    def _cast_dict(self, value: Any, type_hint: Any) -> dict:
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
                    f"Failed to cast {value=} into {k_typ=}, {v_typ=}, error: {e}"
                )
                raise ConversionError(
                    f"Not possible to cast {value} into a dict of keys of type {k_typ}, and values of type {v_typ}, Error: {e}"
                ) from e
        raise LiteralEvalMiscast(
            f"{value} casted as {type(_evaluated_option)} expected {type_hint}"
        )

    def _cast_union(self, value: Any, type_hint: Any) -> Any:
        for typ in get_args(type_hint):
            try:
                return self._cast_value(value, typ)
            except Exception as e:
                logger.debug(f"Failed to cast {value=} into {typ=}, error: {e}")
                continue
        raise ConversionError(f"Not possible to cast {value} into type {type_hint}")
