import configparser
import os

import pytest

from configparser_override import ConfigParserOverride, __version__
from configparser_override.configparser_override import (
    NoPrefixNewDirectStrategy,
    NoPrefixNoNewStrategy,
    OverrideStrategyNotImplementedError,
    PrefixNewEnvNewDirectStrategy,
    PrefixNewEnvStrategy,
    PrefixNoNewStrategy,
    StrategyFactory,
)

TEST_ENV_PREFIX = "TEST_"


@pytest.fixture(autouse=True)
def clear_env():
    # Clear environment variables before and after each test
    keys_to_clear = [
        key
        for key in os.environ
        if key.startswith(TEST_ENV_PREFIX) or key == "DEFAULT_KEY"
    ]

    for key in keys_to_clear:
        del os.environ[key]

    yield

    for key in keys_to_clear:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def config_file(tmp_path):
    config_content = """
    [SECTION1]
    key1 = value1
    key2 = value2

    [SECTION2]
    key3 = value3
    """
    config_path = tmp_path / "config.ini"
    config_path.write_text(config_content)
    return str(config_path)


def test_initialization():
    parser = ConfigParserOverride(env_prefix=TEST_ENV_PREFIX)
    assert parser.env_prefix == TEST_ENV_PREFIX
    assert isinstance(parser.config, configparser.ConfigParser)


def test_read_config_file(config_file):
    parser = ConfigParserOverride()
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "value1"
    assert config["SECTION1"]["key2"] == "value2"
    assert config["SECTION2"]["key3"] == "value3"


def test_env_override(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__KEY1", "override1")
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION2__KEY3", "override3")

    parser = ConfigParserOverride(env_prefix=TEST_ENV_PREFIX)
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "override1"
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "override3"


def test_default_section_override(monkeypatch, tmp_path):
    config_content = """
    [DEFAULT]
    default_key = default_value
    """
    config_path = tmp_path / "default_config.ini"
    config_path.write_text(config_content)

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}DEFAULT_KEY", "override_default")

    parser = ConfigParserOverride(env_prefix=TEST_ENV_PREFIX)
    config = parser.read(filenames=str(config_path))

    assert config.defaults()["default_key"] == "override_default"


def test_version_exits():
    assert isinstance(__version__, str)


def test_direct_override_with_env(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__KEY1", "env_override_value1")

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, SECTION1__key1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_direct_override_with_file(config_file):
    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, SECTION1__key1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_direct_override_with_env_and_file(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__KEY2", "env_override_value2")

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, SECTION1__key1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "env_override_value2"
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_direct_override_default_section(tmp_path):
    config_content = """
    [DEFAULT]
    default_key = default_value
    """
    config_path = tmp_path / "default_config.ini"
    config_path.write_text(config_content)

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, default_key="direct_override_default_value"
    )
    config = parser.read(filenames=str(config_path))

    assert config.defaults()["default_key"] == "direct_override_default_value"


def test_no_prefix_no_new_strategy():
    config = configparser.ConfigParser()
    config.add_section("SECTION1")
    config.set("SECTION1", "option1", "value1")

    overrides = {"SECTION1__option1": "new_value1"}
    strategy = NoPrefixNoNewStrategy(config, "", overrides)
    strategy.execute()

    assert config.get("SECTION1", "option1") == "new_value1"


def test_no_prefix_new_direct_strategy():
    config = configparser.ConfigParser()
    config.add_section("SECTION1")
    config.set("SECTION1", "option1", "value1")

    overrides = {"SECTION2__option2": "new_value2"}
    strategy = NoPrefixNewDirectStrategy(config, "", overrides)
    strategy.execute()

    assert config.get("SECTION2", "option2") == "new_value2"


def test_prefix_no_new_strategy(monkeypatch):
    config = configparser.ConfigParser()
    config.add_section("SECTION1")
    config.set("SECTION1", "option1", "value1")

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__OPTION1", "env_value1")
    overrides = {}
    strategy = PrefixNoNewStrategy(config, TEST_ENV_PREFIX, overrides)
    strategy.execute()

    assert config.get("SECTION1", "option1") == "env_value1"


def test_prefix_new_env_strategy(monkeypatch):
    config = configparser.ConfigParser()

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__OPTION1", "env_value1")
    overrides = {}
    strategy = PrefixNewEnvStrategy(config, TEST_ENV_PREFIX, overrides)
    strategy.execute()

    assert config.get("SECTION1", "option1") == "env_value1"


def test_prefix_new_env_new_direct_strategy(monkeypatch):
    config = configparser.ConfigParser()

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__OPTION1", "env_value1")
    overrides = {"SECTION2__option2": "new_value2"}
    strategy = PrefixNewEnvNewDirectStrategy(config, TEST_ENV_PREFIX, overrides)
    strategy.execute()

    assert config.get("SECTION1", "option1") == "env_value1"
    assert config.get("SECTION2", "option2") == "new_value2"


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


def test_strategy_factory_not_implemented():
    config = configparser.ConfigParser()
    factory = StrategyFactory(config, "", True, True, {})
    with pytest.raises(OverrideStrategyNotImplementedError):
        factory.get_strategy()


def test_config_parser_override(monkeypatch):
    config_override = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX,
        create_new_from_env_prefix=True,
        create_new_from_direct=True,
        SECTION1__option1="override_value1",
    )

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION2__OPTION2", "env_value2")
    config = config_override.read([])
    assert config.get("SECTION1", "option1") == "override_value1"
    assert config.get("SECTION2", "option2") == "env_value2"
