import configparser
import platform
from dataclasses import dataclass

import pytest

from configparser_override import ConfigParserOverride, __version__
from tests._constants import TEST_ENV_PREFIX


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


def test_env_override_with_prefix(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__KEY1", "override1")
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION2__KEY3", "override3")

    parser = ConfigParserOverride(env_prefix=TEST_ENV_PREFIX)
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "override1"
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "override3"


def test_default_section_override_with_env(monkeypatch, config_file_with_default):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}DEFAULT_KEY", "override_default")

    parser = ConfigParserOverride(env_prefix=TEST_ENV_PREFIX)
    config = parser.read(filenames=config_file_with_default)

    assert config.defaults()["default_key"] == "override_default"


def test_version_exists():
    assert isinstance(__version__, str)


def test_direct_override_takes_precedence_over_env(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__KEY1", "env_override_value1")

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, SECTION1__key1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_direct_override_from_file(config_file):
    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, SECTION1__key1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_combined_env_and_direct_override(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__KEY2", "env_override_value2")

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, SECTION1__key1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "env_override_value2"
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_direct_override_in_default_section(config_file_with_default):
    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, default_key="direct_override_default_value"
    )
    config = parser.read(filenames=config_file_with_default)

    assert config.defaults()["default_key"] == "direct_override_default_value"


def test_config_parser_override_with_combined_overrides(monkeypatch):
    config_override = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX,
        create_new_from_env_prefix=True,
        create_new_from_direct=True,
        SECTION1__option1="override_value1",
    )

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION2__OPTION2", "env_value2")
    config = config_override.read([])
    assert config.get("section1", "option1") == "override_value1"
    assert config.get("section2", "option2") == "env_value2"


def test_config_parser_override_with_combined_overrides_case_sensitive(monkeypatch):
    config_override = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX,
        create_new_from_env_prefix=True,
        create_new_from_direct=True,
        case_sensitive_overrides=True,
        SECTION1__option1="override_value1",
    )

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION2__OPTION2", "env_value2")
    config = config_override.read([])
    assert config.get("SECTION1", "option1") == "override_value1"
    assert config.get("SECTION2", "option2") == "env_value2"


def test_case_insensitive_env_override(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}section1__key1", "env_override_value1")

    parser = ConfigParserOverride(env_prefix=TEST_ENV_PREFIX)
    config = parser.read(filenames=config_file)
    p = platform.system()
    if p == "Windows":
        assert config["SECTION1"]["key1"] == "env_override_value1"
        assert config["SECTION1"]["key2"] == "value2"  # Not overridden
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden
    elif p == "Linux":
        assert config["SECTION1"]["key1"] == "value1"  # Linux is case sensitive
        assert config["SECTION1"]["key2"] == "value2"  # Not overridden
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden
    elif p == "Darwin":
        assert config["SECTION1"]["key1"] == "value1"  # MacOS is case sensitive
        assert config["SECTION1"]["key2"] == "value2"  # Not overridden
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_case_insensitive_only_option_env_override(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__key1", "env_override_value1")

    parser = ConfigParserOverride(env_prefix=TEST_ENV_PREFIX)
    config = parser.read(filenames=config_file)
    p = platform.system()
    if p == "Windows":
        assert config["SECTION1"]["key1"] == "env_override_value1"
        assert config["SECTION1"]["key2"] == "value2"  # Not overridden
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden
    elif p == "Linux":
        assert config["SECTION1"]["key1"] == "value1"  # Linux is case sensitive
        assert config["SECTION1"]["key2"] == "value2"  # Not overridden
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden
    elif p == "Darwin":
        assert config["SECTION1"]["key1"] == "value1"  # MacOS is case sensitive
        assert config["SECTION1"]["key2"] == "value2"  # Not overridden
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_case_insensitive_upper_direct_override(config_file):
    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, SECTION1__KEY1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_case_insensitive_lower_direct_override(config_file):
    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, section1__KEY1="direct_override_value1"
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_case_insensitive_lower_direct_multi_override(config_file):
    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX,
        section1__KEY1="direct_override_value1",
        section2__KEY3="direct_override_value3",
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "direct_override_value3"


def test_case_insensitive_lower_direct_not_new(config_file):
    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX,
        create_new_from_direct=False,
        section3__KEY3="direct_override_value3",
        section3__KEY4="direct_override_value4",
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "value1"  # Not overridden
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden
    assert config.has_section("section3") is False


def test_combined_case_insensitive_overrides(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}section1__KEY2", "env_override_value2")

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX,
        SECTION1__KEY1="direct_override_value1",
        create_new_from_direct=True,
        create_new_from_env_prefix=True,
    )
    config = parser.read(filenames=config_file)

    p = platform.system()
    if p == "Windows" or (p == "Linux" or p == "Darwin"):
        assert config["SECTION1"]["key1"] == "direct_override_value1"
        assert config["SECTION1"]["key2"] == "env_override_value2"
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_combined_case_sensitive_overrides(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}section1__KEY2", "env_override_value2")

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX,
        SECTION1__KEY1="direct_override_value1",
        create_new_from_direct=True,
        create_new_from_env_prefix=True,
        case_sensitive_overrides=True,
    )
    config = parser.read(filenames=config_file)

    p = platform.system()
    if p == "Windows":
        assert config["SECTION1"]["key1"] == "direct_override_value1"
        assert config["SECTION1"]["key2"] == "env_override_value2"
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden
    elif p == "Linux" or p == "Darwin":
        assert config["SECTION1"]["key1"] == "direct_override_value1"
        assert config["SECTION1"]["key2"] == "value2"
        assert config["section1"]["key2"] == "env_override_value2"
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_combined_case_sensitive_overrides_no_new(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}section1__KEY2", "env_override_value2")

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX,
        SECTION1__KEY1="direct_override_value1",
        SECTIONNONE__KEY1="direct_override_value_none",
        create_new_from_direct=False,
        create_new_from_env_prefix=False,
        case_sensitive_overrides=True,
    )
    config = parser.read(filenames=config_file)

    p = platform.system()
    if p == "Windows":
        assert config["SECTION1"]["key1"] == "direct_override_value1"
        assert config["SECTION1"]["key2"] == "env_override_value2"
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden
        assert not config.has_section("SECTIONNONE")
        assert not config.has_option("SECTIONNONE", "KEY1")
    elif p == "Linux" or p == "Darwin":
        assert config["SECTION1"]["key1"] == "direct_override_value1"
        assert config["SECTION1"]["key2"] == "value2"
        assert config["SECTION2"]["key3"] == "value3"  # Not overridden
        assert not config.has_section("SECTIONNONE")
        assert not config.has_option("SECTIONNONE", "KEY1")


def test_combined_overrides_with_default_section(monkeypatch, config_file_with_default):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}DEFAULT_KEY", "env_override_default_value")
    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX, default_key="direct_override_default_value"
    )
    config = parser.read(filenames=config_file_with_default)

    assert config.defaults()["default_key"] == "direct_override_default_value"


@pytest.mark.parametrize(
    "env_prefix, create_new_from_env_prefix, create_new_from_direct",
    [
        (TEST_ENV_PREFIX, True, True),
        (TEST_ENV_PREFIX, True, False),
        (TEST_ENV_PREFIX, False, True),
        (TEST_ENV_PREFIX, False, False),
        ("", True, True),
        ("", True, False),
        ("", False, True),
        ("", False, False),
    ],
    ids=[
        "prefix_new_env_new_direct",
        "prefix_new_env",
        "prefix_new_direct",
        "prefix_no_new",
        "no_prefix_new_env_new_direct",
        "no_prefix_new_env",
        "no_prefix_new_direct",
        "no_prefix_no_new",
    ],
)
def test_all_combinations(
    monkeypatch,
    config_file,
    env_prefix,
    create_new_from_env_prefix,
    create_new_from_direct,
):
    monkeypatch.setenv(f"{env_prefix}SECTION1__KEY2", "env_override_value2")
    monkeypatch.setenv(f"{env_prefix}SECTION1__KEY3", "env_override_value3")

    if env_prefix == "" and create_new_from_env_prefix is True:
        with pytest.raises(AssertionError):
            ConfigParserOverride(
                env_prefix=env_prefix,
                create_new_from_env_prefix=create_new_from_env_prefix,
                create_new_from_direct=create_new_from_direct,
                SECTION1__KEY1="direct_override_value1",
                SECTION1__KEY4="direct_override_value4",
            )
    else:
        parser = ConfigParserOverride(
            env_prefix=env_prefix,
            create_new_from_env_prefix=create_new_from_env_prefix,
            create_new_from_direct=create_new_from_direct,
            SECTION1__KEY1="direct_override_value1",
            SECTION1__KEY4="direct_override_value4",
        )
        config = parser.read(filenames=config_file)

        if create_new_from_direct:
            assert config.get("SECTION1", "key1") == "direct_override_value1"
            assert config.get("SECTION1", "key4") == "direct_override_value4"
        else:
            assert config["SECTION1"]["key1"] == "direct_override_value1"
            assert config.has_option(section="SECTION1", option="key4") is False

        if create_new_from_env_prefix and env_prefix != "":
            assert config.get("SECTION1", "key2") == "env_override_value2"
            assert config.get("SECTION1", "key3") == "env_override_value3"
        else:
            assert config.get("SECTION1", "key2") == "env_override_value2"
            assert config.has_option(section="SECTION1", option="key3") is False

        assert config.get("SECTION2", "key3") == "value3"


def test_custom_config_parser():
    custom_parser = configparser.ConfigParser()
    custom_parser.add_section("CUSTOM")
    custom_parser.set("CUSTOM", "key", "custom_value")

    parser = ConfigParserOverride(config_parser=custom_parser)
    config = parser.config

    assert config["CUSTOM"]["key"] == "custom_value"


def test_custom_config_parser_with_combined_overrides(monkeypatch):
    custom_parser = configparser.ConfigParser()
    custom_parser.add_section("CUSTOM")
    custom_parser.set("CUSTOM", "key", "custom_value")

    config_override = ConfigParserOverride(
        config_parser=custom_parser,
        env_prefix=TEST_ENV_PREFIX,
        create_new_from_env_prefix=True,
        create_new_from_direct=True,
        CUSTOM__key="override_value",
    )

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}CUSTOM__NEWKEY", "env_value")
    config = config_override.read([])

    assert config.get("CUSTOM", "key") == "override_value"
    assert config.get("CUSTOM", "newkey") == "env_value"


def test_custom_config_parser_with_file(config_file):
    custom_parser = configparser.ConfigParser()
    custom_parser.add_section("CUSTOM")
    custom_parser.set("CUSTOM", "key", "custom_value")

    parser = ConfigParserOverride(
        config_parser=custom_parser,
        env_prefix=TEST_ENV_PREFIX,
        SECTION1__key1="override_value",
    )
    config = parser.read(filenames=config_file)

    assert config["CUSTOM"]["key"] == "custom_value"
    assert config["SECTION1"]["key1"] == "override_value"
    assert config["SECTION1"]["key2"] == "value2"  # Not overridden
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_custom_config_parser_with_default_section(config_file_with_default):
    custom_parser = configparser.ConfigParser()
    custom_parser.set("DEFAULT", "default_key", "custom_default_value")

    parser = ConfigParserOverride(
        config_parser=custom_parser,
        env_prefix=TEST_ENV_PREFIX,
        default_key="direct_override_default_value",
    )
    config = parser.read(filenames=config_file_with_default)

    assert config.defaults()["default_key"] == "direct_override_default_value"
    assert config["DEFAULT"]["default_key"] == "direct_override_default_value"


def test_custom_config_parser_with_custom_default_section(
    config_file_with_custom_default,
):
    custom_parser = configparser.ConfigParser(default_section="COMMON")

    parser = ConfigParserOverride(
        config_parser=custom_parser,
    )
    config = parser.read(filenames=config_file_with_custom_default)

    assert config.defaults()["default_key1"] == "default_value1"
    assert config["COMMON"]["default_key1"] == "default_value1"


def test_custom_config_parser_with_custom_default_section_override(
    monkeypatch, config_file_with_custom_default
):
    custom_parser = configparser.ConfigParser(default_section="COMMON")
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}DEFAULT_KEY1", "env_value1")

    parser = ConfigParserOverride(
        config_parser=custom_parser,
        env_prefix=TEST_ENV_PREFIX,
        default_key2="direct_override_default_value2",
    )
    config = parser.read(filenames=config_file_with_custom_default)

    assert config.defaults()["default_key2"] == "direct_override_default_value2"
    assert config.defaults()["default_key1"] == "env_value1"


def test_custom_optionxform_insensetive(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__KEY2", "env_override_value2")

    def customform(optionstr: str) -> str:
        return optionstr

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX,
        optionxform=customform,
        section1__key1="direct_override_value1",
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "env_override_value2"
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_custom_optionxform_sensetive(monkeypatch, config_file):
    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__KEY2", "env_override_value2")

    def customform(optionstr: str) -> str:
        return optionstr

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX,
        optionxform=customform,
        SECTION1__KEY1="direct_override_value1",
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["KEY1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "env_override_value2"
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_combined_case_sensitive_overrides_plus_prefix(monkeypatch, config_file):
    monkeypatch.setenv(
        f"{TEST_ENV_PREFIX.lower()}SECTION1__key2", "env_override_value2"
    )

    parser = ConfigParserOverride(
        env_prefix=TEST_ENV_PREFIX.lower(),
        SECTION1__KEY1="direct_override_value1",
        create_new_from_direct=False,
        create_new_from_env_prefix=False,
        case_sensitive_overrides=True,
    )
    config = parser.read(filenames=config_file)

    assert config["SECTION1"]["key1"] == "direct_override_value1"
    assert config["SECTION1"]["key2"] == "env_override_value2"
    assert config["SECTION2"]["key3"] == "value3"  # Not overridden


def test_config_to_dataclass(config_file):
    @dataclass
    class Section1:
        key1: str
        key2: str

    @dataclass
    class Section2:
        key3: str

    @dataclass
    class ConfigFile:
        SECTION1: Section1
        SECTION2: Section2

    parser = ConfigParserOverride()
    parser.read(filenames=config_file)

    dataclass_config = parser.to_dataclass(ConfigFile)
    assert dataclass_config.SECTION1.key1 == "value1"
    assert dataclass_config.SECTION1.key2 == "value2"
    assert dataclass_config.SECTION2.key3 == "value3"
