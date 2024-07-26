from __future__ import annotations

import configparser
import logging
import os
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath

logger = logging.getLogger(__name__)


class ConfigEnvParser:
    def __init__(
        self,
        env_prefix: str = "",
    ):
        """
        Initialize the ConfigEnvParser.

        :param env_prefix: Optional prefix for environment variables, defaults to an
            empty string.
        :type env_prefix: str, optional
        """
        self._config = configparser.ConfigParser()
        self.env_prefix = env_prefix

    def _find_and_override(self):
        """
        Internal method to override configuration values with environment variables.

        This method iterates over all sections and keys in the configuration, and if a
        corresponding environment variable is set, it overrides the configuration value
        with the environment variable's value.
        """
        for section in self._config.sections():
            for key in self._config[section]:
                env_var = (
                    f"{self.env_prefix}__{section}_{key}".upper()
                    if self.env_prefix
                    else f"{section}_{key}".upper()
                )
                if env_var in os.environ:
                    _value = os.environ[env_var]
                    logger.debug(f"Override {section=}, {key=} with {env_var}")
                    self._config.set(section=section, option=key, value=_value)
                else:
                    logger.debug(f"Environment variable {env_var} not set")

        _default_section = self._config.default_section
        for key in self._config.defaults():
            env_var = (
                f"{self.env_prefix}_{key}".upper()
                if self.env_prefix
                else f"{key}".upper()
            )
            if env_var in os.environ:
                _value = os.environ[env_var]
                logger.debug(
                    f"Override section={_default_section}, {key=} with {env_var}"
                )
                self._config.set(section=_default_section, option=key, value=_value)
            else:
                logger.debug(f"Environment variable {env_var} not set")

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
        configuration values with any corresponding environment variables.

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
        self._find_and_override()
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
