import configparser

import pytest

from configparser_override._override_strategy import (
    NewOptionsFromDirectAndEnvStrategy,
    NewOptionsFromDirectStrategy,
    NewOptionsFromEnvStrategy,
    NoNewOptionsStrategy,
)
from configparser_override._strategy_factory import StrategyFactory
from configparser_override.exceptions import OverrideStrategyNotImplementedError
from tests._constants import TEST_ENV_PREFIX


def test_strategy_factory_no_prefix_no_new():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, "", False, False, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, NoNewOptionsStrategy)


def test_strategy_factory_no_prefix_new_direct():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, "", False, True, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, NewOptionsFromDirectStrategy)


def test_strategy_factory_prefix_no_new():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, TEST_ENV_PREFIX, False, False, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, NoNewOptionsStrategy)


def test_strategy_factory_prefix_new_direct():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, TEST_ENV_PREFIX, False, True, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, NewOptionsFromDirectStrategy)


def test_strategy_factory_prefix_new_env():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, TEST_ENV_PREFIX, True, False, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, NewOptionsFromEnvStrategy)


def test_strategy_factory_prefix_new_env_new_direct():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, TEST_ENV_PREFIX, True, True, {})
    strategy = factory.get_strategy()
    assert isinstance(strategy, NewOptionsFromDirectAndEnvStrategy)


def test_strategy_factory_raises_not_implemented_error():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, "", True, "s", {})  # type: ignore
    with pytest.raises(OverrideStrategyNotImplementedError):
        factory.get_strategy()
