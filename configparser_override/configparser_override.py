from __future__ import annotations

import configparser
import logging
from typing import TYPE_CHECKING, Iterable, Type

from configparser_override._strategy_factory import StrategyFactory
from configparser_override.convert import ConfigConverter

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath

    from configparser_override._override_strategy import Strategy
    from configparser_override.types import Dataclass, _optionxform_fn

logger = logging.getLogger(__name__)


class ConfigParserOverride:
    def __init__(
        self,
        env_prefix: str = "",
        create_new_from_env_prefix: bool = True,
        create_new_from_direct: bool = True,
        config_parser: configparser.ConfigParser | None = None,
        case_sensitive_overrides: bool = False,
        optionxform: _optionxform_fn | None = None,
        **overrides: str,
    ):
        """
        Initialize the ConfigParserOverride.

        :param env_prefix: Optional prefix for environment variables,
            defaults to an empty string.
        :type env_prefix: str, optional
        :param create_new_from_env_prefix: Flag to create new configuration
            options from environment variables.
        :type create_new_from_env_prefix: bool, optional
        :param create_new_from_direct: Flag to create new configuration
            options from direct overrides.
        :type create_new_from_direct: bool, optional
        :param config_parser: Optional ConfigParser object to be used,
            defaults to None.
        :type config_parser: configparser.ConfigParser, optional
        :param case_sensitive_overrides: Flag to indicate if overrides should
            be case sensitive.
        :type case_sensitive_overrides: bool, optional
        :param optionxform: Optional function to transform option strings.
        :type optionxform: _optionxform_fn | None, optional
        :param overrides: Keyword arguments to directly override configuration values.
        :type overrides: dict[str, str | None]
        """

        self.env_prefix = env_prefix
        self.create_new_from_env_prefix = create_new_from_env_prefix
        self.create_new_from_direct = create_new_from_direct
        self.case_sensitive_overrides = case_sensitive_overrides
        self.optionxform = optionxform
        self.overrides = overrides

        # Configure ConfigParser and align optionxform for consistency in later
        # inferance for overrides
        if config_parser is None:
            self._config = configparser.ConfigParser()
            if self.optionxform is not None:
                self._config.optionxform = self.optionxform  # type: ignore
        else:
            self._config = config_parser
            self.optionxform = self._config.optionxform

    def _get_override_strategy(self) -> Strategy:
        """
        Get the appropriate override strategy based on initialization parameters.

        :return: The appropriate strategy instance.
        :rtype: Strategy
        """
        return StrategyFactory(
            self._config,
            self.env_prefix,
            self.create_new_from_env_prefix,
            self.create_new_from_direct,
            self.overrides,
            self.case_sensitive_overrides,
            self.optionxform,
        ).get_strategy()

    def read(
        self,
        filenames: StrOrBytesPath | Iterable[StrOrBytesPath],
        encoding: str | None = None,
    ) -> list[str]:
        """
        Read configuration from one or more files and override with environment
        variables if set.

        This method is a wrapper around :py:meth:`configparser.ConfigParser.read` that
        reads the specified filenames in order. After reading the files, it overrides
        configuration values with corresponding environment variables and direct
        overrides passed during initialization.

        :param filenames: A single filename or an iterable of filenames to read.
        :type filenames: :py:class:`_typeshed.StrOrBytesPath` or
            Iterable[:py:class:`_typeshed.StrOrBytesPath`]
        :param encoding: The encoding to use for reading the files, defaults to None.
        :type encoding: str, optional
        :return: List of successfully parsed files
        :rtype: list[str]

        **Examples:**

        .. code-block:: python

            >>> parser_override = ConfigParserOverride(test_option='value')
            >>> parser_override.read(['example.ini'])
            >>> config = parser_override.config
            >>> config.get('DEFAULT', 'test_option')
            'value'


        """
        files_read = self._config.read(filenames=filenames, encoding=encoding)
        strategy = self._get_override_strategy()
        strategy.execute()
        return files_read

    @property
    def config(self) -> configparser.ConfigParser:
        """
        Property to access the configuration.

        This can be used to modify the property of the configparser object and
        also set and get options manually.

        :return: The :py:class:`configparser.ConfigParser` object
            with the configuration.
        :rtype: :py:class:`configparser.ConfigParser`

        **Examples:**

        Get an option after parsing and overrides:

        .. code-block:: python

            >>> config = ConfigParserOverride(test_option='value')
            >>> config.read(['example.ini'])
            >>> config.get('DEFAULT', 'test_option')
            'value'

        Can also be used like just like regular ConfigParser:

        .. code-block:: python

            >>> parser_override = ConfigParserOverride()
            >>> config = parser_override.config
            >>> config.set('section', 'option', 'value')
            >>> config.get('section', 'option')
            'value'

        """
        return self._config

    def to_dataclass(self, dataclass: Type[Dataclass]) -> Dataclass:
        """
        Convert the configuration data to a dataclass instance.

        Can be useful to validate that the configuration adheres to the expected format
        and leverage various typing frameworks, eg. integrations with your text editor.

        :param dataclass: The dataclass type to convert the configuration data into.
        :type dataclass: _dataclass
        :return: An instance of the dataclass populated with the configuration data.
        :rtype: _dataclass

        **Examples:**

        .. code-block:: python

            >>> from dataclasses import dataclass

            >>> @dataclass
            ... class Section1:
            ...     key: str

            >>> @dataclass
            ... class ExampleConfig:
            ...     section1: Section1

            >>> config_parser_override = ConfigParserOverride(section1__key="a string")
            >>> config_parser_override.read()
            >>> config_as_dataclass = config_parser_override.to_dataclass(ExampleConfig)
            >>> assert config_as_dataclass.section1.key == "a string" # True
        """

        return ConfigConverter(self._config).config_to_dataclass(dataclass)
