import configparser
import os

import pytest

from configparser_override import __version__
from configparser_override.configparser_override import ConfigParserOverride

TEST_ENV_PREFIX = "TEST"


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
    [section1]
    key1 = value1
    key2 = value2

    [section2]
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

    assert config["section1"]["key1"] == "value1"
    assert config["section1"]["key2"] == "value2"
    assert config["section2"]["key3"] == "value3"


def test_env_override(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}__SECTION1_KEY1", "override1")
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}__SECTION2_KEY3", "override3")

    parser = ConfigParserOverride(env_prefix=TEST_ENV_PREFIX)
    config = parser.read(filenames=config_file)

    assert config["section1"]["key1"] == "override1"
    assert config["section1"]["key2"] == "value2"  # Not overridden
    assert config["section2"]["key3"] == "override3"


def test_default_section_override(monkeypatch, tmp_path):
    config_content = """
    [DEFAULT]
    default_key = default_value
    """
    config_path = tmp_path / "default_config.ini"
    config_path.write_text(config_content)

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}_DEFAULT_KEY", "override_default")

    parser = ConfigParserOverride(env_prefix=TEST_ENV_PREFIX)
    config = parser.read(filenames=str(config_path))

    assert config.defaults()["default_key"] == "override_default"


def test_version_exits():
    assert isinstance(__version__, str)


def test_direct_override_with_env(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}__SECTION1_KEY1", "env_override_value1")

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, section1__key1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["section1"]["key1"] == "direct_override_value1"
    assert config["section1"]["key2"] == "value2"  # Not overridden
    assert config["section2"]["key3"] == "value3"  # Not overridden


def test_direct_override_with_file(config_file):
    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, section1__key1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["section1"]["key1"] == "direct_override_value1"
    assert config["section1"]["key2"] == "value2"  # Not overridden
    assert config["section2"]["key3"] == "value3"  # Not overridden


def test_direct_override_with_env_and_file(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}__SECTION1_KEY2", "env_override_value2")

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, section1__key1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["section1"]["key1"] == "direct_override_value1"
    assert config["section1"]["key2"] == "env_override_value2"
    assert config["section2"]["key3"] == "value3"  # Not overridden


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
