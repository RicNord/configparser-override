import logging

logger = logging.getLogger(__name__)


class ConfigParserOverrideError(Exception):
    pass


class OverrideStrategyNotImplementedError(ConfigParserOverrideError):
    """Exception raised when an unimplemented strategy is requested."""

    pass


class SectionNotFound(ConfigParserOverrideError):
    """Exception raised when a section is not found in the ConfigParser"""

    pass


class ConversionError(ConfigParserOverrideError):
    """Exception raised for errors of casting a string to typehinted value(s)"""

    pass


class LiteralEvalMiscast(ConfigParserOverrideError):
    """
    Exception raised when ast.literal_eval casts the string to a unexpected data type
    """

    pass


class NoConfigFilesFoundError(ConfigParserOverrideError):
    """
    Exception raised when no configuration files can be found
    """

    pass
