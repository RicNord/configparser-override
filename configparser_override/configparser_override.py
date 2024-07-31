from __future__ import annotations

import configparser
import enum
import logging
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath

logger = logging.getLogger(__name__)


class OverrideStrategyNotImplementedError(Exception):
    pass


class Strategy(ABC):
    def __init__(
        self,
        config: configparser.ConfigParser,
        env_prefix: str,
        overrides: dict[str, str | None],
    ):
        self._config = config
        self._env_prefix = env_prefix
        self._overrides = overrides

    @abstractmethod
    def execute(self):
        pass

    def collect_env_vars_with_prefix(self, prefix: str) -> dict[str, str]:
        return {
            key.strip(prefix): value
            for key, value in os.environ.items()
            if key.startswith(prefix)
        }

    def parse_key(self, key: str) -> tuple[str, str]:
        parts = key.split("__", 1)
        if len(parts) == 1:
            return "DEFAULT", parts[0]
        return parts[0], parts[1]

    def override_env(self, create_new_options: bool):
        if create_new_options:
            env_vars = self.collect_env_vars_with_prefix(self._env_prefix)
            for key, value in env_vars.items():
                section, option = self.parse_key(key)
                if not self._config.has_section(section=section):
                    self._config.add_section(section=section)
                self._config.set(section=section, option=option, value=value)

        else:
            for section in self._config.sections():
                for option in self._config[section]:
                    env_var = (
                        f"{self._env_prefix}{section}__{option}"
                        if self._env_prefix != ""
                        else f"{section}__{option}"
                    )
                    if env_var in os.environ:
                        _value = os.environ[env_var]
                        logger.debug(f"Override {section=}, {option=} with {env_var}")
                        self._config.set(section=section, option=option, value=_value)
                    else:
                        logger.debug(f"Environment variable {env_var} not set")

            _default_section = self._config.default_section
            for option in self._config.defaults():
                env_var = (
                    f"{self._env_prefix}_{option}"
                    if self._env_prefix != ""
                    else f"{option}"
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
        if create_new_options:
            for key, value in self._overrides.items():
                section, option = self.parse_key(key)
                if not self._config.has_section(section=section):
                    self._config.add_section(section=section)
                self._config.set(section=section, option=option, value=value)

        else:
            for key, value in self._overrides.items():
                section, option = self.parse_key(key)
                if self._config.has_section(section) and self._config.has_option(
                    section, option
                ):
                    logger.debug(
                        f"Override {section=}, {option=} with direct assignment"
                    )
                    self._config.set(section=section, option=option, value=value)
                else:
                    logger.debug(f"New direct assignment {section=} {option=} ignored")


class NoPrefixNoNewStrategy(Strategy):
    def execute(self):
        for key, value in self._overrides.items():
            section, option = self.parse_key(key)
            if self._config.has_section(section) and self._config.has_option(
                section, option
            ):
                self._config.set(section, option, value)


class NoPrefixNewDirectStrategy(Strategy):
    def execute(self):
        self.override_env(create_new_options=False)
        self.override_direct(create_new_options=True)


class PrefixNoNewStrategy(Strategy):
    def execute(self):
        self.override_env(create_new_options=False)
        self.override_direct(create_new_options=False)


class PrefixNewEnvStrategy(Strategy):
    def execute(self):
        env_vars = self.collect_env_vars_with_prefix(self._env_prefix)
        for key, value in env_vars.items():
            section, option = self.parse_key(key)
            if not self._config.has_section(section):
                self._config.add_section(section)
            self._config.set(section, option, value)


class PrefixNewDirectStrategy(Strategy):
    def execute(self):
        self.override_env(create_new_options=False)
        self.override_direct(create_new_options=True)


class PrefixNewEnvNewDirectStrategy(Strategy):
    def execute(self):
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
        overrides: dict[str, str | None],
    ):
        self.config = config
        self.env_prefix = env_prefix
        self.create_new_from_env_prefix = create_new_from_env_prefix
        self.create_new_from_direct = create_new_from_direct
        self.overrides = overrides

    def get_strategy(self) -> Strategy:
        """
        Determine the appropriate strategy based on initialization parameters.

        :return: The appropriate strategy instance.
        """

        NO_PREFIX_NO_NEW = (
            self.env_prefix == ""
            and self.create_new_from_env_prefix is False
            and self.create_new_from_direct is False
        )
        NO_PREFIX_NEW_DIRECT = (
            self.env_prefix == ""
            and self.create_new_from_env_prefix is False
            and self.create_new_from_direct is True
        )
        PREFIX_NO_NEW = (
            self.env_prefix != ""
            and self.create_new_from_env_prefix is False
            and self.create_new_from_direct is False
        )
        PREFIX_NEW_ENV = (
            self.env_prefix != ""
            and self.create_new_from_env_prefix is True
            and self.create_new_from_direct is False
        )
        PREFIX_NEW_DIRECT = (
            self.env_prefix != ""
            and self.create_new_from_env_prefix is False
            and self.create_new_from_direct is True
        )
        PREFIX_NEW_ENV_NEW_DIRECT = (
            self.env_prefix != ""
            and self.create_new_from_env_prefix is True
            and self.create_new_from_direct is True
        )

        if NO_PREFIX_NO_NEW:
            return OverrideStrategies.NO_PREFIX_NO_NEW.value(
                self.config, self.env_prefix, self.overrides
            )
        elif NO_PREFIX_NEW_DIRECT:
            return OverrideStrategies.NO_PREFIX_NEW_DIRECT.value(
                self.config, self.env_prefix, self.overrides
            )
        elif PREFIX_NO_NEW:
            return OverrideStrategies.PREFIX_NO_NEW.value(
                self.config, self.env_prefix, self.overrides
            )
        elif PREFIX_NEW_ENV:
            return OverrideStrategies.PREFIX_NEW_ENV.value(
                self.config, self.env_prefix, self.overrides
            )
        elif PREFIX_NEW_DIRECT:
            return OverrideStrategies.PREFIX_NEW_DIRECT.value(
                self.config, self.env_prefix, self.overrides
            )
        elif PREFIX_NEW_ENV_NEW_DIRECT:
            return OverrideStrategies.PREFIX_NEW_ENV_NEW_DIRECT.value(
                self.config, self.env_prefix, self.overrides
            )

        raise OverrideStrategyNotImplementedError()


class ConfigParserOverride:
    def __init__(
        self,
        env_prefix: str = "",
        create_new_from_env_prefix: bool = False,
        create_new_from_direct: bool = True,
        **overrides: str | None,
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
        :param overrides: Keyword arguments to directly override configuration values.
        """

        self.env_prefix = env_prefix
        self.create_new_from_env_prefix = create_new_from_env_prefix
        self.create_new_from_direct = create_new_from_direct
        self.overrides = overrides

        if self.create_new_from_env_prefix:
            assert self.env_prefix, "To set new configuration options from environment variables a prefix has to be used!"

        self._config = configparser.ConfigParser()

    def _get_override_strategy(self) -> Strategy:
        return StrategyFactory(
            self._config,
            self.env_prefix,
            self.create_new_from_env_prefix,
            self.create_new_from_direct,
            self.overrides,
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
        """
        self._config.read(filenames=filenames, encoding=encoding)
        strategy = self._get_override_strategy()
        strategy.execute()
        return self.config

    @property
    def config(self) -> configparser.ConfigParser:
        """
        Property to access the configuration.

        :return: The :py:class:`configparser.ConfigParser` object
            with the configuration.
        :rtype: :py:class:`configparser.ConfigParser`
        """
        return self._config
