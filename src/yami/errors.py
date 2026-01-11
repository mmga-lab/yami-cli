"""Error codes and classification for yami CLI."""

from __future__ import annotations

import json
from enum import Enum


class ErrorCode(str, Enum):
    """Structured error codes for Agent parsing."""

    # Connection errors
    CONNECTION_ERROR = "CONNECTION_ERROR"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_ARGUMENT = "MISSING_ARGUMENT"
    INVALID_FORMAT = "INVALID_FORMAT"
    SCHEMA_ERROR = "SCHEMA_ERROR"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # Operation errors
    OPERATION_FAILED = "OPERATION_FAILED"
    TIMEOUT = "TIMEOUT"
    CONFLICT = "CONFLICT"

    # Data errors
    DATA_ERROR = "DATA_ERROR"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    IMPORT_ERROR = "IMPORT_ERROR"

    # Internal errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


ERROR_HINTS: dict[ErrorCode, str] = {
    ErrorCode.CONNECTION_ERROR: "Check if Milvus server is running and URI is correct",
    ErrorCode.CONNECTION_TIMEOUT: "Increase timeout with --timeout or check network",
    ErrorCode.AUTHENTICATION_ERROR: "Verify your token with 'yami connect <uri> --token <token>'",
    ErrorCode.NOT_FOUND: "Use 'yami collection list' to see available collections",
    ErrorCode.ALREADY_EXISTS: "Use a different name or drop the existing resource first",
    ErrorCode.IMPORT_ERROR: "Install missing dependency with 'uv add <package>'",
    ErrorCode.FILE_NOT_FOUND: "Check if the file path is correct and file exists",
    ErrorCode.MISSING_ARGUMENT: "Use 'yami <command> --help' to see required arguments",
    ErrorCode.INVALID_FORMAT: "Check JSON/SQL syntax is valid",
    ErrorCode.PERMISSION_DENIED: "Check user permissions with 'yami role list'",
    ErrorCode.SCHEMA_ERROR: "Check field DSL syntax: name:type[:modifier]",
}


def classify_exception(e: Exception) -> tuple[ErrorCode, str | None]:
    """Classify an exception into an error code with optional hint.

    Args:
        e: The exception to classify.

    Returns:
        A tuple of (ErrorCode, hint string or None).
    """
    error_msg = str(e).lower()

    # File errors
    if isinstance(e, FileNotFoundError):
        return ErrorCode.FILE_NOT_FOUND, ERROR_HINTS[ErrorCode.FILE_NOT_FOUND]
    if isinstance(e, ImportError):
        return ErrorCode.IMPORT_ERROR, ERROR_HINTS[ErrorCode.IMPORT_ERROR]

    # JSON errors
    if isinstance(e, json.JSONDecodeError):
        return ErrorCode.INVALID_FORMAT, "Check JSON syntax is valid"

    # Connection errors
    if "connection" in error_msg or "connect" in error_msg:
        if "timeout" in error_msg:
            return ErrorCode.CONNECTION_TIMEOUT, ERROR_HINTS[ErrorCode.CONNECTION_TIMEOUT]
        return ErrorCode.CONNECTION_ERROR, ERROR_HINTS[ErrorCode.CONNECTION_ERROR]

    if "timeout" in error_msg:
        return ErrorCode.TIMEOUT, "Operation timed out, try again or increase timeout"

    if "authentication" in error_msg or "unauthorized" in error_msg or "unauthenticated" in error_msg:
        return ErrorCode.AUTHENTICATION_ERROR, ERROR_HINTS[ErrorCode.AUTHENTICATION_ERROR]

    # Resource errors
    if "not found" in error_msg or "does not exist" in error_msg or "doesn't exist" in error_msg or "can't find" in error_msg:
        return ErrorCode.NOT_FOUND, ERROR_HINTS[ErrorCode.NOT_FOUND]

    if "already exist" in error_msg:
        return ErrorCode.ALREADY_EXISTS, ERROR_HINTS[ErrorCode.ALREADY_EXISTS]

    if "permission" in error_msg or "denied" in error_msg or "forbidden" in error_msg:
        return ErrorCode.PERMISSION_DENIED, ERROR_HINTS[ErrorCode.PERMISSION_DENIED]

    # Validation errors
    if "invalid" in error_msg or "validation" in error_msg:
        return ErrorCode.VALIDATION_ERROR, None

    if "required" in error_msg or "missing" in error_msg:
        return ErrorCode.MISSING_ARGUMENT, ERROR_HINTS[ErrorCode.MISSING_ARGUMENT]

    # Schema errors
    if "schema" in error_msg or "field" in error_msg and "type" in error_msg:
        return ErrorCode.SCHEMA_ERROR, ERROR_HINTS[ErrorCode.SCHEMA_ERROR]

    # Default
    return ErrorCode.UNKNOWN_ERROR, None


def get_error_hint(code: ErrorCode) -> str | None:
    """Get the hint for an error code."""
    return ERROR_HINTS.get(code)
