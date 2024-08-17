import logging
import os
import platform
from pathlib import Path
from typing import List, Optional

from configparser_override.exceptions import NoConfigFilesFoundError

logger = logging.getLogger(__name__)


def _log_and_return_if_exists(file_path: Path) -> Optional[Path]:
    if file_path.exists():
        logger.debug(f"Found config file: {file_path}")
        return file_path
    return None


def _unix_collect_home_config(subdir: str, file_name: str) -> Optional[Path]:
    home = Path.home()
    xdg_config_home = Path(os.getenv("XDG_CONFIG_HOME", home / ".config"))
    home_config = xdg_config_home / subdir / file_name
    return _log_and_return_if_exists(home_config)


def _unix_collect_system_config(
    subdir: str, file_name: str, bare_etc: bool = False
) -> List[Path]:
    config_file_list = []
    if bare_etc:
        file_path = Path("/etc") / subdir / file_name
        config_file = _log_and_return_if_exists(file_path)
        return [config_file] if config_file else []

    xdg_config_dirs = [
        Path(dir) for dir in os.getenv("XDG_CONFIG_DIRS", "/etc/xdg").split(":")
    ]
    for dir in xdg_config_dirs:
        file_path = dir / subdir / file_name
        config_file = _log_and_return_if_exists(file_path)
        if config_file:
            config_file_list.append(config_file)
    config_file_list.reverse()
    return config_file_list


def _windows_collect_home_config(subdir: str, file_name: str) -> Optional[Path]:
    appdata = os.getenv("APPDATA")
    if appdata:
        home_config = Path(appdata) / subdir / file_name
        return _log_and_return_if_exists(home_config)
    return None


def _windows_collect_system_config(subdir: str, file_name: str) -> List[Path]:
    programdata = os.getenv("PROGRAMDATA")
    config_file_list = []
    if programdata:
        file_path = Path(programdata) / subdir / file_name
        config_file = _log_and_return_if_exists(file_path)
        if config_file:
            config_file_list.append(config_file)
    return config_file_list


def config_file_collector(
    file_name: str,
    app_name: str = "",
    merge_files: bool = True,
    allow_no_found_files: bool = True,
    bare_etc: bool = False,
) -> List[Path]:

    system = platform.system()

    if system == "Windows":
        config_files = _windows_collect_system_config(app_name, file_name)
        home_config = _windows_collect_home_config(app_name, file_name)
    else:
        config_files = _unix_collect_system_config(app_name, file_name, bare_etc)
        home_config = _unix_collect_home_config(app_name, file_name)

    if home_config:
        config_files.append(home_config)

    if not config_files and not allow_no_found_files:
        raise NoConfigFilesFoundError(
            f"No configuration files found for file_name={file_name}, app_name={app_name}"
        )
    # Return single most prioritized file if no merge, else entire list of
    # found files with highest prioritized file last
    return [config_files.pop()] if config_files and not merge_files else config_files
