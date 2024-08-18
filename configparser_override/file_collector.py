import logging
import os
import platform
from pathlib import Path
from typing import List, Optional

from configparser_override.exceptions import NoConfigFilesFoundError

logger = logging.getLogger(__name__)


def _log_and_return_if_exists(file_path: Path) -> Optional[Path]:
    """
    Check if the given file path exists and log as found if so.

    :param file_path: Path to the configuration file.
    :type file_path: Path
    :return: The file path if it exists, otherwise None.
    :rtype: Optional[Path]
    """
    if file_path.exists():
        logger.debug(f"Found config file: {file_path}")
        return file_path
    return None


def _unix_collect_home_config(subdir: str, file_name: str) -> Optional[Path]:
    """
    Collect Unix home directory configuration file.

    :param subdir: Subdirectory under the home config path.
    :type subdir: str
    :param file_name: Name of the configuration file.
    :type file_name: str
    :return: Path to the home configuration file if it exists, otherwise None.
    :rtype: Optional[Path]
    """
    home = Path.home()
    xdg_config_home = Path(os.getenv("XDG_CONFIG_HOME", home / ".config"))
    home_config = xdg_config_home / subdir / file_name
    return _log_and_return_if_exists(home_config)


def _unix_collect_system_config(
    subdir: str, file_name: str, bare_etc: bool = False
) -> List[Path]:
    """
    Collect Unix system configuration files.

    :param subdir: Subdirectory under the system config path.
    :type subdir: str
    :param file_name: Name of the configuration file.
    :type file_name: str
    :param bare_etc: Look in bare `/etc` directory if True.
    :type bare_etc: bool
    :return: List of paths to system configuration files.
    :rtype: List[Path]
    """
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
    """
    Collect Windows home directory configuration file.

    :param subdir: Subdirectory under the home config path.
    :type subdir: str
    :param file_name: Name of the configuration file.
    :type file_name: str
    :return: Path to the home configuration file if it exists, otherwise None.
    :rtype: Optional[Path]
    """
    appdata = os.getenv("APPDATA")
    if appdata:
        home_config = Path(appdata) / subdir / file_name
        return _log_and_return_if_exists(home_config)
    return None


def _windows_collect_system_config(subdir: str, file_name: str) -> List[Path]:
    """
    Collect Windows system configuration files.

    :param subdir: Subdirectory under the system config path.
    :type subdir: str
    :param file_name: Name of the configuration file.
    :type file_name: str
    :return: List of paths to system configuration files.
    :rtype: List[Path]
    """
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
    only_most_important_file: bool = False,
    allow_no_found_files: bool = True,
    bare_etc: bool = False,
) -> List[Path]:
    """
    Collect configuration files from conventional locations.

    If multiple files are returned, they are in order of ascending priority
    (most important file last).

    :param file_name: Name of the configuration file.
    :type file_name: str
    :param app_name: Name of the app, used as a subdirectory.
    :type app_name: str
    :param only_most_important_file: Only return the most important (prioritized) file,
        eg. home directory config files is more important than system wide config file
    :type only_most_important_file: bool
    :param allow_no_found_files: Whether to allow no found files without raising an error.
    :type allow_no_found_files: bool
    :param bare_etc: Look in bare `/etc` directory if True (Unix only).
    :type bare_etc: bool
    :return: List of paths to configuration files.
    :rtype: List[Path]
    :raises NoConfigFilesFoundError: If no config files are found and `allow_no_found_files` is False.

    .. code-block:: python

        from pathlib import Path
        from your_module import config_file_collector

        # Collect configuration files for the my_app application with
        # the name config.ini
        config_files = config_file_collector(
            file_name="config.ini",
            app_name="my_app",
            only_most_important_file=False,
            allow_no_found_files=True,
        )

        # Output the found configuration files
        for config_file in config_files:
            print(f"Found config file: {config_file}")
        # Example output:
        #    Found config file: /etc/xdg/my_app/config.ini
        #    Found config file: /home/user/.config/my_app/config.ini

    """
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

    return (
        [config_files.pop()]
        if config_files and only_most_important_file
        else config_files
    )
