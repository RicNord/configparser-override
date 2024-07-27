__version__ = "0.1.0"

import logging

from configparser_override.configparser_override import ConfigParserOverride

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ["__version__", "ConfigParserOverride"]
