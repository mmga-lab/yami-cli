"""Custom exceptions for Yami CLI."""


class YamiError(Exception):
    """Base exception for Yami CLI."""

    pass


class ConnectionError(YamiError):
    """Error connecting to Milvus server."""

    pass


class ConfigError(YamiError):
    """Error in configuration."""

    pass


class ProfileNotFoundError(ConfigError):
    """Specified profile not found."""

    pass
