from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from configparser_override.exceptions import NoConfigFilesFoundError
from configparser_override.file_collector import (
    _log_and_return_if_exists,
    _unix_collect_home_config,
    _unix_collect_system_config,
    _windows_collect_home_config,
    _windows_collect_system_config,
    config_file_collector,
)


# Mock logger to avoid actual logging during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch("configparser_override.file_collector.logger"):
        yield


def test_log_and_return_if_exists_file_exists():
    path = MagicMock(spec=Path)
    path.exists.return_value = True
    assert _log_and_return_if_exists(path) == path


def test_log_and_return_if_exists_file_does_not_exist():
    path = MagicMock(spec=Path)
    path.exists.return_value = False
    assert _log_and_return_if_exists(path) is None


@patch("configparser_override.file_collector.Path.home")
@patch("configparser_override.file_collector.os.getenv")
def test_unix_collect_home_config(mock_getenv, mock_home):
    mock_home.return_value = Path("/home/testuser")
    mock_getenv.return_value = Path("/home/testuser/.config")
    subdir = "testapp"
    file_name = "config.ini"

    with patch(
        "configparser_override.file_collector._log_and_return_if_exists"
    ) as mock_log_and_return_if_exists:
        mock_log_and_return_if_exists.return_value = Path(
            "/home/testuser/.config/testapp/config.ini"
        )
        result = _unix_collect_home_config(subdir, file_name)
        assert result == Path("/home/testuser/.config/testapp/config.ini")


@patch("configparser_override.file_collector.os.getenv")
@patch("configparser_override.file_collector.Path.exists")
def test_unix_collect_system_config(mock_path_exists, mock_os_getenv):
    mock_os_getenv.return_value = "/etc/xdg"

    mock_path_exists.return_value = True
    subdir = "testapp"
    file_name = "config.ini"
    result = _unix_collect_system_config(subdir, file_name)
    assert result == [Path("/etc/xdg/testapp/config.ini")]


@patch("configparser_override.file_collector.os.getenv")
@patch("configparser_override.file_collector.Path.exists")
def test_unix_collect_system_multi_config(mock_path_exists, mock_os_getenv):
    # First value is most important
    mock_os_getenv.return_value = "/etc/xdg:/etc"

    mock_path_exists.return_value = True
    subdir = "testapp"
    file_name = "config.ini"
    result = _unix_collect_system_config(subdir, file_name)
    # Reverse importance for configpraser override default
    assert result == [
        Path("/etc/testapp/config.ini"),
        Path("/etc/xdg/testapp/config.ini"),
    ]


@patch("configparser_override.file_collector.os.getenv")
@patch("configparser_override.file_collector.Path.exists")
def test_unix_collect_system_multi_config_not_exist(mock_path_exists, mock_os_getenv):
    # First value is most important
    mock_os_getenv.return_value = "/etc/xdg:/etc"

    mock_path_exists.return_value = False
    subdir = "testapp"
    file_name = "config.ini"
    result = _unix_collect_system_config(subdir, file_name)
    # Reverse importance for configpraser override default
    assert result == []


@patch("configparser_override.file_collector.Path.exists")
def test_unix_collect_system_bare_etc(mock_path_exists):
    mock_path_exists.return_value = True
    subdir = "testapp"
    file_name = "config.ini"
    result = _unix_collect_system_config(subdir, file_name, bare_etc=True)
    # Reverse importance for configpraser override default
    assert result == [
        Path("/etc/testapp/config.ini"),
    ]


@patch("configparser_override.file_collector.os.getenv")
@patch("configparser_override.file_collector.Path.exists")
def test_windows_collect_home_config(mock_path_exists, mock_os_getenv):
    mock_os_getenv.return_value = "C:/Users/testuser/AppData/Roaming"
    mock_path_exists.return_value = True
    subdir = "testapp"
    file_name = "config.ini"
    result = _windows_collect_home_config(subdir, file_name)
    assert result == Path("C:/Users/testuser/AppData/Roaming/testapp/config.ini")


@patch("configparser_override.file_collector.os.getenv")
def test_windows_collect_home_config_not_exist(mock_os_getenv):
    mock_os_getenv.return_value = None
    subdir = "testapp"
    file_name = "config.ini"
    result = _windows_collect_home_config(subdir, file_name)
    assert result is None


@patch("configparser_override.file_collector.os.getenv")
@patch("configparser_override.file_collector.Path.exists")
def test_windows_collect_system_config(mock_path_exists, mock_os_getenv):
    mock_os_getenv.return_value = "C:/ProgramData"
    mock_path_exists.return_value = True
    subdir = "testapp"
    file_name = "config.ini"
    result = _windows_collect_system_config(subdir, file_name)
    assert result == [Path("C:/ProgramData/testapp/config.ini")]


@patch("configparser_override.file_collector.os.getenv")
@patch("configparser_override.file_collector.Path.exists")
def test_windows_collect_system_config_not_exist_path(mock_path_exists, mock_os_getenv):
    mock_os_getenv.return_value = "C:/ProgramData"
    mock_path_exists.return_value = False
    subdir = "testapp"
    file_name = "config.ini"
    result = _windows_collect_system_config(subdir, file_name)
    assert result == []


@patch("configparser_override.file_collector.os.getenv")
def test_windows_collect_system_config_not_exist(mock_os_getenv):
    mock_os_getenv.return_value = None
    subdir = "testapp"
    file_name = "config.ini"
    result = _windows_collect_system_config(subdir, file_name)
    assert result == []


@patch("configparser_override.file_collector.platform.system", return_value="Windows")
@patch("configparser_override.file_collector._windows_collect_system_config")
@patch("configparser_override.file_collector._windows_collect_home_config")
def test_config_file_collector_windows(
    mock_home_config, mock_system_config, mock_platform
):
    mock_system_config.return_value = [Path("C:/ProgramData/testapp/config.ini")]
    mock_home_config.return_value = Path(
        "C:/Users/testuser/AppData/Roaming/testapp/config.ini"
    )
    result = config_file_collector("config.ini", "testapp")
    assert result == [
        Path("C:/ProgramData/testapp/config.ini"),
        Path("C:/Users/testuser/AppData/Roaming/testapp/config.ini"),
    ]


@patch("configparser_override.file_collector.platform.system", return_value="Linux")
@patch("configparser_override.file_collector._unix_collect_system_config")
@patch("configparser_override.file_collector._unix_collect_home_config")
def test_config_file_collector_linux(
    mock_home_config, mock_system_config, mock_platform
):
    mock_system_config.return_value = [Path("/etc/xdg/testapp/config.ini")]
    mock_home_config.return_value = Path("/home/testuser/.config/testapp/config.ini")
    result = config_file_collector("config.ini", "testapp")
    assert result == [
        Path("/etc/xdg/testapp/config.ini"),
        Path("/home/testuser/.config/testapp/config.ini"),
    ]


@patch("configparser_override.file_collector.platform.system", return_value="Darwin")
@patch("configparser_override.file_collector._unix_collect_system_config")
@patch("configparser_override.file_collector._unix_collect_home_config")
def test_config_file_collector_darwin(
    mock_home_config, mock_system_config, mock_platform
):
    mock_system_config.return_value = [Path("/etc/xdg/testapp/config.ini")]
    mock_home_config.return_value = Path("/home/testuser/.config/testapp/config.ini")
    result = config_file_collector("config.ini", "testapp")
    assert result == [
        Path("/etc/xdg/testapp/config.ini"),
        Path("/home/testuser/.config/testapp/config.ini"),
    ]


@patch("configparser_override.file_collector.platform.system", return_value="Linux")
@patch("configparser_override.file_collector._unix_collect_system_config")
@patch("configparser_override.file_collector._unix_collect_home_config")
def test_config_file_collector_linux_only_1_file(
    mock_home_config, mock_system_config, mock_platform
):
    mock_system_config.return_value = [
        Path("/etc/xdg/testapp/config.ini"),
    ]
    mock_home_config.return_value = Path("/home/testuser/.config/testapp/config.ini")
    result = config_file_collector(
        "config.ini", "testapp", only_most_important_file=True
    )
    assert result == [
        Path("/home/testuser/.config/testapp/config.ini"),
    ]


@patch("configparser_override.file_collector.platform.system", return_value="Linux")
@patch("configparser_override.file_collector._unix_collect_system_config")
@patch("configparser_override.file_collector._unix_collect_home_config")
def test_config_file_collector_linux_multiple_system_files(
    mock_home_config, mock_system_config, mock_platform
):
    mock_system_config.return_value = [
        Path("/etc/xdg/testapp/config.ini"),
        Path("/etc/testapp/config.ini"),
    ]
    mock_home_config.return_value = Path("/home/testuser/.config/testapp/config.ini")
    result = config_file_collector("config.ini", "testapp")
    assert result == [
        Path("/etc/xdg/testapp/config.ini"),
        Path("/etc/testapp/config.ini"),
        Path("/home/testuser/.config/testapp/config.ini"),
    ]


@patch("configparser_override.file_collector.platform.system", return_value="Linux")
@patch("configparser_override.file_collector._unix_collect_system_config")
@patch("configparser_override.file_collector._unix_collect_home_config")
def test_config_file_collector_no_files_found(
    mock_home_config, mock_system_config, mock_platform
):
    mock_system_config.return_value = []
    mock_home_config.return_value = None
    with pytest.raises(NoConfigFilesFoundError):
        config_file_collector("config.ini", "testapp", allow_no_found_files=False)
