"""Custom exceptions for Yami CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yami.core.error_catalog import ErrorCode


class YamiError(Exception):
    """Base exception for Yami CLI.

    Supports error codes and contextual information for better error messages.
    """

    def __init__(
        self,
        message: str,
        code: ErrorCode | None = None,
        context: dict | None = None,
    ):
        super().__init__(message)
        self.message = message
        self._code = code
        self.context = context or {}

    @property
    def code(self) -> ErrorCode:
        """Get error code."""
        if self._code is not None:
            return self._code
        from yami.core.error_catalog import ErrorCode

        return ErrorCode.UNKNOWN

    def with_context(self, **kwargs) -> YamiError:
        """Add context to the error."""
        self.context.update(kwargs)
        return self


class ConnectionError(YamiError):
    """Error connecting to Milvus server."""

    def __init__(
        self,
        message: str,
        code: ErrorCode | None = None,
        uri: str | None = None,
    ):
        super().__init__(message, code)
        if uri:
            self.context["uri"] = uri

    @property
    def code(self) -> ErrorCode:
        """Get error code, auto-classifying if not set."""
        if self._code is not None:
            return self._code
        from yami.core.error_catalog import classify_connection_error

        return classify_connection_error(self.message)


class ConfigError(YamiError):
    """Error in configuration."""

    @property
    def code(self) -> ErrorCode:
        """Get error code."""
        if self._code is not None:
            return self._code
        from yami.core.error_catalog import ErrorCode

        return ErrorCode.CONFIG_INVALID


class ProfileNotFoundError(ConfigError):
    """Specified profile not found."""

    def __init__(self, profile_name: str, message: str | None = None):
        msg = message or f"Profile '{profile_name}' not found"
        super().__init__(msg)
        self.profile_name = profile_name
        self.context["profile"] = profile_name

    @property
    def code(self) -> ErrorCode:
        """Get error code."""
        from yami.core.error_catalog import ErrorCode

        return ErrorCode.PROFILE_NOT_FOUND


class CollectionError(YamiError):
    """Error related to collection operations."""

    def __init__(
        self,
        message: str,
        code: ErrorCode | None = None,
        collection: str | None = None,
    ):
        super().__init__(message, code)
        if collection:
            self.context["collection"] = collection

    @property
    def code(self) -> ErrorCode:
        """Get error code, auto-classifying if not set."""
        if self._code is not None:
            return self._code
        from yami.core.error_catalog import classify_milvus_error

        return classify_milvus_error(self.message)


class SchemaError(YamiError):
    """Error related to schema operations."""

    @property
    def code(self) -> ErrorCode:
        """Get error code."""
        if self._code is not None:
            return self._code
        from yami.core.error_catalog import ErrorCode

        return ErrorCode.SCHEMA_INVALID


class DataError(YamiError):
    """Error related to data operations."""

    @property
    def code(self) -> ErrorCode:
        """Get error code, auto-classifying if not set."""
        if self._code is not None:
            return self._code
        from yami.core.error_catalog import classify_milvus_error

        return classify_milvus_error(self.message)


class AuthError(YamiError):
    """Authentication error."""

    @property
    def code(self) -> ErrorCode:
        """Get error code."""
        from yami.core.error_catalog import ErrorCode

        return ErrorCode.AUTH_FAILED


class OperationError(YamiError):
    """Error during a Milvus operation."""

    @property
    def code(self) -> ErrorCode:
        """Get error code, auto-classifying if not set."""
        if self._code is not None:
            return self._code
        from yami.core.error_catalog import classify_milvus_error

        return classify_milvus_error(self.message)
