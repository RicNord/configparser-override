from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from configparser_override._override_strategy import OverrideStrategies, Strategy
from configparser_override.exceptions import OverrideStrategyNotImplementedError

if TYPE_CHECKING:
    import configparser

    from configparser_override.types import _optionxform_fn

logger = logging.getLogger(__name__)


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
            (True, False): OverrideStrategies.NEW_OPTIONS_FROM_ENV,
            (False, True): OverrideStrategies.NEW_OPTIONS_FROM_DIRECT,
            (True, True): OverrideStrategies.NEW_OPTIONS_FROM_DIRECT_AND_ENV,
            (False, False): OverrideStrategies.NO_NEW_OPTIONS,
        }
        key = (
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
