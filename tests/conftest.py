import os

import pytest

from tests._constants import TEST_ENV_PREFIX


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


@pytest.fixture
def config_file_with_default(tmp_path):
    config_content = """
    [DEFAULT]
    default_key = default_value

    [SECTION1]
    key1 = value1
    """
    config_path = tmp_path / "config_with_default.ini"
    config_path.write_text(config_content)
    return str(config_path)


@pytest.fixture
def config_file_with_custom_default(tmp_path):
    config_content = """
    [COMMON]
    default_key1 = default_value1
    default_key2 = default_value2
    default_key3 = default_value3

    [SECTION1]
    key1 = value1
    key2 = value2

    [SECTION2]
    key3 = value3
    """
    config_path = tmp_path / "config_with_custom_default.ini"
    config_path.write_text(config_content)
    return str(config_path)
