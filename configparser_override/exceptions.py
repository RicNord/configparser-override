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
