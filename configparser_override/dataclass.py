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
    Check if a given type hint is an optional type.

    :param type_hint: The type hint to check.
    :type type_hint: Any
    :return: True if the type hint is optional, False otherwise.
    :rtype: bool
    """
    return get_origin(type_hint) in [Union, UnionType] and type(None) in get_args(
        type_hint
    )


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
    ) -> None:
        self.config = config
        if boolean_states:
            self.boolean_states = boolean_states
        else:
            self.boolean_states = self.config.BOOLEAN_STATES

    def config_to_dict(self) -> dict[str, dict[str, str]]:
        """
        Convert the configuration data to a nested dictionary.

        :return: The configuration data as a dictionary.
        :rtype: dict[str, dict[str, str]]
        """
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
        """
        Convert the configuration data to a dataclass instance.

        :param dataclass: The dataclass type to convert the configuration data into.
        :type dataclass: _dataclass
        :return: An instance of the dataclass populated with the configuration data.
        :rtype: _dataclass
        """
        config_dict = self.config_to_dict()
        return self._dict_to_dataclass(
            input_dict=config_dict,
            dataclass=dataclass,
        )

    def _dict_to_dataclass(self, input_dict: dict, dataclass: _dataclass) -> _dataclass:
        """
        Convert a dictionary to a dataclass instance.

        :param input_dict: The input dictionary to convert.
        :type input_dict: dict
        :param dataclass: The dataclass type to convert the dictionary into.
        :type dataclass: _dataclass
        :return: An instance of the dataclass populated with the dictionary data.
        :rtype: _dataclass
        :raises ValueError: If the input object is not a dataclass or required
            fields are missing.
        """
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
        Trey to cast a value to a given type hint.

        :param value: The value to cast.
        :type value: Any
        :param type_hint: The type hint to cast the value to.
        :type type_hint: Any
        :return: The value cast to the specified type hint.
        :rtype: Any
        :raises ValueError: If the type hint is unsupported.
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
        Cast a value to a boolean.

        :param value: The value to cast.
        :type value: Any
        :return: The value cast to a boolean.
        :rtype: bool
        :raises ValueError: If the value cannot be cast to a boolean.
        """
        if str(value).lower() in self.boolean_states:
            return self.boolean_states[str(value).lower()]
        else:
            raise ValueError(f"{value=} not in possible {self.boolean_states=}")

    def _cast_list(self, value: Any, type_hint: Any) -> list:
        """
        Cast a value to a list of a specified type.

        :param value: The value to cast.
        :type value: Any
        :param type_hint: The type hint for the list elements.
        :type type_hint: Any
        :return: The value cast to a list of the specified type.
        :rtype: list
        :raises ConversionError: If the value cannot be cast to a list of hinted types.
        :raises LiteralEvalMiscast: If the value cannot be evaluated to the
            expected type.
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
        Cast a value to a dictionary of specified types for keys and values.

        :param value: The value to cast.
        :type value: Any
        :param type_hint: The type hint for the dictionary keys and values.
        :type type_hint: Any
        :return: The value cast to a dictionary of the specified types.
        :rtype: dict
        :raises ConversionError: If the value cannot be cast to a dictionary of
            hinted types
        :raises LiteralEvalMiscast: If the value cannot be evaluated to the
            expected type.
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
        Cast a value to one of the types in a union type hint.

        :param value: The value to cast.
        :type value: Any
        :param type_hint: The union type hint.
        :type type_hint: Any
        :return: The value cast to one of the types in the union.
        :rtype: Any
        :raises ConversionError: If the value cannot be cast to any of the types in
            the union.
        """
        for typ in get_args(type_hint):
            try:
                return self._cast_value(value, typ)
            except Exception as e:
                logger.debug(f"Faild to cast {value=} into {typ=}, error: {e}")
                continue
        raise ConversionError(f"Not possible to cast {value} into type {type_hint}")
