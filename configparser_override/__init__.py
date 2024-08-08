__version__ = "0.5.0"

import logging

from configparser_override.configparser_override import ConfigParserOverride
from configparser_override.convert import ConfigConverter

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ["__version__", "ConfigParserOverride", "ConfigConverter"]
