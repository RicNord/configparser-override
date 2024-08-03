import configparser

import pytest

from configparser_override.exceptions import OverrideStrategyNotImplementedError
from configparser_override.override_strategy import (
    NoPrefixNewDirectStrategy,
    NoPrefixNoNewStrategy,
    PrefixNewDirectStrategy,
    PrefixNewEnvNewDirectStrategy,
    PrefixNewEnvStrategy,
    PrefixNoNewStrategy,
)
from configparser_override.strategy_factory import StrategyFactory
from tests._constants import TEST_ENV_PREFIX


def test_strategy_factory_no_prefix_no_new():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, "", False, False, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, NoPrefixNoNewStrategy)


def test_strategy_factory_no_prefix_new_direct():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, "", False, True, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, NoPrefixNewDirectStrategy)


def test_strategy_factory_prefix_no_new():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, TEST_ENV_PREFIX, False, False, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, PrefixNoNewStrategy)


def test_strategy_factory_prefix_new_direct():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, TEST_ENV_PREFIX, False, True, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, PrefixNewDirectStrategy)


def test_strategy_factory_prefix_new_env():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, TEST_ENV_PREFIX, True, False, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, PrefixNewEnvStrategy)


def test_strategy_factory_prefix_new_env_new_direct():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, TEST_ENV_PREFIX, True, True, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, PrefixNewEnvNewDirectStrategy)


def test_strategy_factory_raises_not_implemented_error():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, "", True, True, {})
    with pytest.raises(OverrideStrategyNotImplementedError):
        factory.get_strategy()
