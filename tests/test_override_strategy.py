import configparser
import platform

import pytest

from configparser_override._override_strategy import (
    NewOptionsFromDirectAndEnvStrategy,
    NewOptionsFromDirectStrategy,
    NewOptionsFromEnvStrategy,
    NoNewOptionsStrategy,
    _lowercase_optionxform,
)
from configparser_override.exceptions import SectionNotFound
from tests._constants import TEST_ENV_PREFIX


def test_lowercase_optionxform():
    assert _lowercase_optionxform("TEST") == "test"
    assert _lowercase_optionxform("TesT") == "test"
    assert _lowercase_optionxform("test") == "test"


def test_no_prefix_no_new_strategy_executes_overrides():
    config = configparser.ConfigParser()
    config.add_section("SECTION1")
    config.set("SECTION1", "option1", "value1")

    overrides = {"SECTION1__option1": "new_value1"}
    strategy = NoNewOptionsStrategy(config, "", overrides)
    strategy.execute()

    assert config.get("SECTION1", "option1") == "new_value1"


def test_no_prefix_new_direct_strategy_creates_new_options():
    config = configparser.ConfigParser()
    config.add_section("SECTION1")
    config.set("SECTION1", "option1", "value1")

    overrides = {"section2__option2": "new_value2"}
    strategy = NewOptionsFromDirectStrategy(config, "", overrides)
    strategy.execute()

    assert config.get("section2", "option2") == "new_value2"


def test_no_prefix_new_direct_strategy_creates_new_options_with_sensetive_case():
    config = configparser.ConfigParser()
    config.add_section("SECTION1")
    config.set("SECTION1", "option1", "value1")

    overrides = {"SECTION2__OPTION2": "new_value2"}
    strategy = NewOptionsFromDirectStrategy(config, "", overrides, True)
    strategy.execute()

    assert config.get("SECTION2", "OPTION2") == "new_value2"


def test_prefix_new_direct_overrides_existing_options(monkeypatch):
    config = configparser.ConfigParser()
    config.add_section("SECTION1")
    config.set("SECTION1", "option1", "value1")
    config.set("SECTION1", "option2", "value2")

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__OPTION1", "env_value1")
    overrides = {"section1__option3": "direct_value3"}
    strategy = NewOptionsFromDirectStrategy(config, TEST_ENV_PREFIX, overrides)
    strategy.execute()

    assert config.get("SECTION1", "option1") == "env_value1"
    assert config.get("SECTION1", "option2") == "value2"
    assert config.get("SECTION1", "option3") == "direct_value3"


def test_prefix_no_new_strategy_overrides_existing_options(monkeypatch):
    config = configparser.ConfigParser()
    config.add_section("SECTION1")
    config.set("SECTION1", "option1", "value1")

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__OPTION1", "env_value1")
    overrides = {}
    strategy = NoNewOptionsStrategy(config, TEST_ENV_PREFIX, overrides)
    strategy.execute()

    assert config.get("SECTION1", "option1") == "env_value1"


def test_prefix_new_env_strategy_creates_new_options_from_env(monkeypatch):
    config = configparser.ConfigParser()

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__OPTION1", "env_value1")
    overrides = {}
    strategy = NewOptionsFromEnvStrategy(config, TEST_ENV_PREFIX, overrides)
    strategy.execute()

    assert config.get("section1", "option1") == "env_value1"


def test_prefix_new_env_strategy_creates_new_options_from_env_case_sensetive_upper(
    monkeypatch,
):
    config = configparser.ConfigParser()

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__OPTION1", "env_value1")
    overrides = {}
    strategy = NewOptionsFromEnvStrategy(config, TEST_ENV_PREFIX, overrides, True)
    strategy.execute()

    assert config.get("SECTION1", "option1") == "env_value1"


def test_prefix_new_env_strategy_creates_new_options_from_env_case_sensetive_lower(
    monkeypatch,
):
    config = configparser.ConfigParser()

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}section1__option1", "env_value1")
    overrides = {}
    strategy = NewOptionsFromEnvStrategy(config, TEST_ENV_PREFIX, overrides, True)
    strategy.execute()

    p = platform.system()
    if p == "Windows":
        assert (
            config.get("SECTION1", "option1") == "env_value1"
        )  # Env var stored as capital for win
    elif p == "Linux" or p == "Darwin":
        assert config.get("section1", "option1") == "env_value1"


def test_prefix_new_env_new_direct_strategy_creates_both(monkeypatch):
    config = configparser.ConfigParser()

    monkeypatch.setenv(f"{TEST_ENV_PREFIX}SECTION1__OPTION1", "env_value1")
    overrides = {"SECTION2__option2": "new_value2"}
    strategy = NewOptionsFromDirectAndEnvStrategy(config, TEST_ENV_PREFIX, overrides)
    strategy.execute()

    assert config.get("section1", "option1") == "env_value1"
    assert config.get("section2", "option2") == "new_value2"


def test_parse_key_case_insensitive():
    config = configparser.ConfigParser()
    strategy = NoNewOptionsStrategy(config, "", {})
    section, option = strategy.parse_key("SECTION__OPTION")
    assert section == "SECTION"
    assert option == "option"


def test_decide_env_var_case_insensitive():
    config = configparser.ConfigParser()
    strategy = NoNewOptionsStrategy(config, "", {})
    env_var = strategy.decide_env_var("", "SECTION", "OPTION")
    assert env_var == "SECTION__OPTION"


def test_decide_env_var_case_sensitive():
    config = configparser.ConfigParser()
    strategy = NoNewOptionsStrategy(config, "", {}, case_sensitive_overrides=True)
    env_var = strategy.decide_env_var("", "section", "OPTION")
    assert env_var == "section__OPTION"


def test_decide_env_var_case_insensitive_prefix():
    config = configparser.ConfigParser()
    strategy = NoNewOptionsStrategy(config, "PREFIX_", {})
    env_var = strategy.decide_env_var("PREFIX_", "SECTION", "OPTION")
    assert env_var == "PREFIX_SECTION__OPTION"


def test_decide_env_var_case_sensitive_prefix():
    config = configparser.ConfigParser()
    strategy = NoNewOptionsStrategy(
        config, "PREFIX_", {}, case_sensitive_overrides=True
    )
    env_var = strategy.decide_env_var("PREFIX_", "section", "OPTION")
    assert env_var == "PREFIX_section__OPTION"


def test_has_section_case_insensitive():
    config = configparser.ConfigParser()
    config.add_section("section")
    strategy = NoNewOptionsStrategy(config, "", {})
    assert strategy.has_section("section")
    assert strategy.has_section("SECTION")


def test_has_section_case_sensitive():
    config = configparser.ConfigParser()
    config.add_section("SECTION")
    strategy = NoNewOptionsStrategy(config, "", {}, case_sensitive_overrides=True)
    assert strategy.has_section("SECTION")
    assert not strategy.has_section("section")


def test_get_existing_section_case_insensitive():
    config = configparser.ConfigParser()
    config.add_section("section")
    strategy = NoNewOptionsStrategy(config, "", {})
    assert strategy.get_existing_section_case_insensitive("SECTION") == "section"


def test_get_existing_section_case_sensitive():
    config = configparser.ConfigParser()
    config.add_section("SECTION")
    strategy = NoNewOptionsStrategy(config, "", {})
    with pytest.raises(SectionNotFound):
        strategy.get_existing_section_case_insensitive("NOT_A_SECTION")


def test_collect_env_vars_with_prefix(monkeypatch):
    monkeypatch.setenv("PREFIX_SECTION__OPTION", "value")
    strategy = NoNewOptionsStrategy(configparser.ConfigParser(), "PREFIX_", {})
    env_vars = strategy.collect_env_vars_with_prefix("PREFIX_")
    assert env_vars == {"SECTION__OPTION": "value"}
