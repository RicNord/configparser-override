from __future__ import annotations

import enum
import logging
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Mapping

from configparser_override.exceptions import SectionNotFound

if TYPE_CHECKING:
    import configparser

    from configparser_override.types import _optionxform_fn

logger = logging.getLogger(__name__)


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

    def override_env(self, create_new_options: bool):
        """
        Override configuration values using environment variables.

        :param create_new_options: Flag to indicate if new options can be created.
        :type create_new_options: bool
        """
        if create_new_options:
            env_vars = (
                self.collect_env_vars_with_prefix(self._env_prefix)
                if self._env_prefix != ""
                else {}
            )
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


class NewOptionsFromEnvStrategy(Strategy):
    def execute(self):
        self.override_env(create_new_options=True)
        self.override_direct(create_new_options=False)


class NewOptionsFromDirectStrategy(Strategy):
    def execute(self):
        self.override_env(create_new_options=False)
        self.override_direct(create_new_options=True)


class NewOptionsFromDirectAndEnvStrategy(Strategy):
    def execute(self):
        self.override_env(create_new_options=True)
        self.override_direct(create_new_options=True)


class NoNewOptionsStrategy(Strategy):
    def execute(self):
        self.override_env(create_new_options=False)
        self.override_direct(create_new_options=False)


class OverrideStrategies(enum.Enum):
    NEW_OPTIONS_FROM_ENV = NewOptionsFromEnvStrategy
    NEW_OPTIONS_FROM_DIRECT = NewOptionsFromDirectStrategy
    NEW_OPTIONS_FROM_DIRECT_AND_ENV = NewOptionsFromDirectAndEnvStrategy
    NO_NEW_OPTIONS = NoNewOptionsStrategy
