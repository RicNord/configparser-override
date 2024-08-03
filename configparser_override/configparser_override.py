from __future__ import annotations

import configparser
import enum
import logging
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterable, Mapping, Protocol

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath

logger = logging.getLogger(__name__)


class _optionxform_fn(Protocol):
    def __call__(self, optionstr: str) -> str: ...  # pragma: no cover


class OverrideStrategyNotImplementedError(Exception):
    """Exception raised when an unimplemented strategy is requested."""

    pass


class SectionNotFound(Exception):
    """Exception raised when a section is not found in the ConfigParser"""

    pass


def _lowercase_optionxform(optionstr: str) -> str:
    """
    Convert the given option string to lowercase.

    :param optionstr: The option string to be converted.
    :type optionstr: str
    :return: The lowercase version of the option string.
    :rtype: str
    """
    return optionstr.lower()


class Strategy(ABC):
    def __init__(
        self,
        config: configparser.ConfigParser,
        env_prefix: str,
        overrides: Mapping[str, str],
        case_sensitive_overrides: bool = False,
        optionxform_fn: _optionxform_fn | None = None,
    ):
        """
        Initialize the base Strategy class.

        :param config: The ConfigParser object to be used.
        :type config: configparser.ConfigParser
        :param env_prefix: Prefix for environment variables.
        :type env_prefix: str
        :param overrides: Mapping of override keys and values.
        :type overrides: Mapping[str, str | None]
        :param case_sensitive_overrides: Flag to indicate if overrides should
            be case sensitive.
        :type case_sensitive_overrides: bool, optional
        :param optionxform_fn: Optional function to transform option strings.
        :type optionxform_fn: _optionxform_fn | None, optional
        """
        self._config = config
        self._env_prefix = env_prefix
        self._overrides = overrides
        self.case_sensitive_overrides = case_sensitive_overrides
        if optionxform_fn is None:
            self.optionxform_fn = _lowercase_optionxform
        else:
            self.optionxform_fn = optionxform_fn

    @abstractmethod
    def execute(self):
        """Execute the strategy. Must be implemented by subclasses."""
        pass

    def collect_env_vars_with_prefix(self, prefix: str) -> dict[str, str]:
        """
        Collect environment variables that start with the given prefix.

        :param prefix: The prefix to filter environment variables.
        :type prefix: str
        :return: Dictionary of environment variables with the prefix removed.
        :rtype: dict[str, str]
        """
        if self.case_sensitive_overrides:
            return {
                key[len(prefix) :]: value
                for key, value in os.environ.items()
                if key.startswith(prefix)
            }
        return {
            key[len(prefix) :]: value
            for key, value in os.environ.items()
            if key.startswith(prefix.upper())
        }

    def parse_key(self, key: str) -> tuple[str, str]:
        """
        Parse a given key to extract the section and option.

        ConfigParser stores all options as lowercase by default, hence the option part
        is standardized to be lowercase unless a `optionxform` functions is specified.

        :param key: The key to parse.
        :type key: str
        :return: A tuple containing the section and option.
        :rtype: tuple[str, str]
        """
        parts = key.split("__", 1)
        if len(parts) == 1:
            return self._config.default_section, self.optionxform_fn(parts[0])
        return parts[0], self.optionxform_fn(parts[1])

    def decide_env_var(self, prefix: str, section: str, option: str) -> str:
        """
        Determine the appropriate environment variable name based on the given
        prefix, section, and option.

        :param prefix: The prefix for environment variables.
        :type prefix: str
        :param section: The section in the configuration.
        :type section: str
        :param option: The option in the configuration.
        :type option: str
        :return: The environment variable name.
        :rtype: str

        .. note::
            This method is aware of case-sensitivity setting

        """
        if self.case_sensitive_overrides:
            env_var = (
                f"{prefix}{section}__{option}"
                if section != self._config.default_section
                else f"{prefix}{option}"
            )
        else:
            env_var = (
                f"{prefix.upper()}{section.upper()}__{option.upper()}"
                if section.lower() != self._config.default_section.lower()
                else f"{prefix.upper()}{option.upper()}"
            )
        return env_var

    def override_env(self, create_new_options: bool):
        """
        Override configuration values using environment variables.

        :param create_new_options: Flag to indicate if new options can be created.
        :type create_new_options: bool
        """
        if create_new_options:
            env_vars = self.collect_env_vars_with_prefix(self._env_prefix)
            for key, value in env_vars.items():
                self.override_and_add_new(key=key, value=value)
        else:
            for section in self._config.sections():
                for option in self._config[section]:
                    env_var = self.decide_env_var(self._env_prefix, section, option)
                    if env_var in os.environ:
                        _value = os.environ[env_var]
                        logger.debug(f"Override {section=}, {option=} with {env_var}")
                        self._config.set(section=section, option=option, value=_value)
                    else:
                        logger.debug(f"Environment variable {env_var} not set")

            _default_section = self._config.default_section
            for option in self._config.defaults():
                env_var = self.decide_env_var(
                    self._env_prefix, _default_section, option
                )
                if env_var in os.environ:
                    _value = os.environ[env_var]
                    logger.debug(
                        f"Override section={_default_section}, {option=} with {env_var}"
                    )
                    self._config.set(
                        section=_default_section, option=option, value=_value
                    )
                else:
                    logger.debug(f"Environment variable {env_var} not set")

    def has_section(self, section: str) -> bool:
        """
        Check if the section exists or is the default section.

        :param section: The section name to check.
        :type section: str
        :return: True if the section exists, False otherwise.
        :rtype: bool

        .. note::
            This method is aware of case-sensitivity setting

        """
        if self.case_sensitive_overrides:
            return (
                self._config.has_section(section)
                or section == self._config.default_section
            )
        return (
            section.lower() in (sect.lower() for sect in self._config.sections())
            or section.lower() == self._config.default_section.lower()
        )

    def get_existing_section_case_insensitive(self, section: str) -> str:
        """
        Get the existing section name in a case-insensitive manner.

        :param section: The section name to search for.
        :type section: str
        :return: The actual section name in the configuration.
        :rtype: str
        :raises SectionNotFound: If section is not found.
        """
        if section.lower() == self._config.default_section.lower():
            return self._config.default_section
        for sect in self._config.sections():
            if sect.lower() == section.lower():
                return sect
        raise SectionNotFound(f"Section {section} not found.")

    def override_and_add_new(self, key: str, value: str):
        section, option = self.parse_key(key)
        if self.case_sensitive_overrides:
            if not self.has_section(section):
                self._config.add_section(section=section)
            self._config.set(section=section, option=option, value=value)
        else:
            if not self.has_section(section):
                self._config.add_section(section=section.lower())
                self._config.set(section=section.lower(), option=option, value=value)
            else:
                _section = self.get_existing_section_case_insensitive(section)
                self._config.set(section=_section, option=option, value=value)

    def override_direct(self, create_new_options: bool):
        """
        Override configuration values using direct overrides.

        :param create_new_options: Flag to indicate if new options can be created.
        :type create_new_options: bool
        """
        if create_new_options:
            for key, value in self._overrides.items():
                self.override_and_add_new(key=key, value=value)

        else:
            for key, value in self._overrides.items():
                section, option = self.parse_key(key)
                if self.case_sensitive_overrides:
                    if self.has_section(section) and self._config.has_option(
                        section, option
                    ):
                        logger.debug(
                            f"Override {section=}, {option=} with direct assignment"
                        )
                        self._config.set(section=section, option=option, value=value)
                    else:
                        logger.debug(
                            f"New direct assignment {section=} {option=} ignored"
                        )
                else:
                    if self.has_section(section):
                        section = self.get_existing_section_case_insensitive(section)
                        if self._config.has_option(section, option):
                            logger.debug(
                                f"Override {section=}, {option=} with direct assignment"
                            )
                            self._config.set(
                                section=section, option=option, value=value
                            )
                        else:
                            logger.debug(
                                f"New direct assignment {section=} {option=} ignored"
                            )


class NoPrefixNoNewStrategy(Strategy):
    def execute(self):
        """Execute strategy: No prefix and no new options."""
        self.override_env(create_new_options=False)
        self.override_direct(create_new_options=False)


class NoPrefixNewDirectStrategy(Strategy):
    def execute(self):
        """Execute strategy: No prefix and allow new direct options."""
        self.override_env(create_new_options=False)
        self.override_direct(create_new_options=True)


class PrefixNoNewStrategy(Strategy):
    def execute(self):
        """Execute strategy: Prefix used and no new options."""
        self.override_env(create_new_options=False)
        self.override_direct(create_new_options=False)


class PrefixNewEnvStrategy(Strategy):
    def execute(self):
        """Execute strategy: Prefix used and allow new environment options."""
        self.override_env(create_new_options=True)
        self.override_direct(create_new_options=False)


class PrefixNewDirectStrategy(Strategy):
    def execute(self):
        """Execute strategy: Prefix used and allow new direct options."""
        self.override_env(create_new_options=False)
        self.override_direct(create_new_options=True)


class PrefixNewEnvNewDirectStrategy(Strategy):
    def execute(self):
        """Execute strategy: Prefix used and allow new environment and direct options."""
        self.override_env(create_new_options=True)
        self.override_direct(create_new_options=True)


class OverrideStrategies(enum.Enum):
    NO_PREFIX_NO_NEW = NoPrefixNoNewStrategy
    NO_PREFIX_NEW_DIRECT = NoPrefixNewDirectStrategy
    PREFIX_NO_NEW = PrefixNoNewStrategy
    PREFIX_NEW_ENV = PrefixNewEnvStrategy
    PREFIX_NEW_DIRECT = PrefixNewDirectStrategy
    PREFIX_NEW_ENV_NEW_DIRECT = PrefixNewEnvNewDirectStrategy


class StrategyFactory:
    def __init__(
        self,
        config: configparser.ConfigParser,
        env_prefix: str,
        create_new_from_env_prefix: bool,
        create_new_from_direct: bool,
        overrides: dict[str, str],
        case_sensitive_overrides: bool = False,
        optionxform: _optionxform_fn | None = None,
    ):
        """
        Initialize the StrategyFactory.

        :param config: The ConfigParser object to be used.
        :type config: configparser.ConfigParser
        :param env_prefix: Prefix for environment variables.
        :type env_prefix: str
        :param create_new_from_env_prefix: Flag to create new options from environment
            variables.
        :type create_new_from_env_prefix: bool
        :param create_new_from_direct: Flag to create new options from direct overrides.
        :type create_new_from_direct: bool
        :param overrides: Dictionary of override keys and values.
        :type overrides: dict[str, str | None]
        :param case_sensitive_overrides: Flag to indicate if overrides should
            be case sensitive.
        :type case_sensitive_overrides: bool, optional
        :param optionxform: Optional function to transform option strings.
        :type optionxform: _optionxform_fn | None, optional
        """
        self.config = config
        self.env_prefix = env_prefix
        self.create_new_from_env_prefix = create_new_from_env_prefix
        self.create_new_from_direct = create_new_from_direct
        self.overrides = overrides
        self.case_sensitive_overrides = case_sensitive_overrides
        self.optionxform = optionxform

    def get_strategy(self) -> Strategy:
        """
        Determine and return the appropriate strategy based on initialization
        parameters.

        :return: The appropriate strategy instance.
        :rtype: Strategy
        :raises OverrideStrategyNotImplementedError: If no matching strategy is found.
        """
        strategies = {
            (False, False, False): OverrideStrategies.NO_PREFIX_NO_NEW,
            (False, False, True): OverrideStrategies.NO_PREFIX_NEW_DIRECT,
            (True, False, False): OverrideStrategies.PREFIX_NO_NEW,
            (True, True, False): OverrideStrategies.PREFIX_NEW_ENV,
            (True, False, True): OverrideStrategies.PREFIX_NEW_DIRECT,
            (True, True, True): OverrideStrategies.PREFIX_NEW_ENV_NEW_DIRECT,
        }
        key = (
            bool(self.env_prefix),
            self.create_new_from_env_prefix,
            self.create_new_from_direct,
        )
        strategy_cls = strategies.get(key)
        if strategy_cls is None:
            raise OverrideStrategyNotImplementedError()
        return strategy_cls.value(
            self.config,
            self.env_prefix,
            self.overrides,
            self.case_sensitive_overrides,
            self.optionxform,
        )


class ConfigParserOverride:
    def __init__(
        self,
        env_prefix: str = "",
        create_new_from_env_prefix: bool = False,
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

        if self.create_new_from_env_prefix:
            assert self.env_prefix, "To set new configuration options from environment variables a prefix has to be used!"

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
    ) -> configparser.ConfigParser:
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
        :return: The :py:class:`configparser.ConfigParser` object with the loaded and
            possibly overridden configuration.
        :rtype: :py:class:`configparser.ConfigParser`

        **Examples:**

        .. code-block:: python

            >>> parser_override = ConfigParserOverride(test_option='value')
            >>> config = parser_override.read(['example.ini'])
            >>> config.get('DEFAULT', 'test_option')
            'value'


        """
        self._config.read(filenames=filenames, encoding=encoding)
        strategy = self._get_override_strategy()
        strategy.execute()
        return self.config

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
