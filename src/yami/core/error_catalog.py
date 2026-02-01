"""Error catalog with error codes and fix suggestions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorCode(str, Enum):
    """Error codes for Yami CLI."""

    # Connection errors (E001-E009)
    CONNECTION_FAILED = "E001"
    CONNECTION_TIMEOUT = "E002"
    AUTH_FAILED = "E003"
    SERVER_UNREACHABLE = "E004"

    # Configuration errors (E010-E019)
    PROFILE_NOT_FOUND = "E010"
    CONFIG_INVALID = "E011"
    CONFIG_MISSING = "E012"

    # Schema errors (E020-E029)
    COLLECTION_NOT_FOUND = "E020"
    SCHEMA_INVALID = "E021"
    FIELD_NOT_FOUND = "E022"
    VECTOR_DIMENSION_MISMATCH = "E023"

    # Data errors (E030-E039)
    DATA_INVALID = "E030"
    DATA_TYPE_MISMATCH = "E031"
    PRIMARY_KEY_DUPLICATE = "E032"

    # Operation errors (E040-E049)
    OPERATION_FAILED = "E040"
    PERMISSION_DENIED = "E041"
    RESOURCE_NOT_LOADED = "E042"

    # General errors (E090-E099)
    UNKNOWN = "E099"


@dataclass
class ErrorInfo:
    """Error information with code, message, and suggestions."""

    code: ErrorCode
    title: str
    causes: list[str]
    suggestions: list[str]


# Error catalog with detailed information
ERROR_CATALOG: dict[ErrorCode, ErrorInfo] = {
    ErrorCode.CONNECTION_FAILED: ErrorInfo(
        code=ErrorCode.CONNECTION_FAILED,
        title="Connection Failed",
        causes=[
            "Milvus server is not running",
            "URI format incorrect (expected: http://host:port)",
            "Network/firewall blocking connection",
        ],
        suggestions=[
            "yami doctor                         # Run diagnostics",
            "yami config profile test <name>     # Validate profile",
            "Check if Milvus is running: docker ps | grep milvus",
        ],
    ),
    ErrorCode.CONNECTION_TIMEOUT: ErrorInfo(
        code=ErrorCode.CONNECTION_TIMEOUT,
        title="Connection Timeout",
        causes=[
            "Server is slow to respond",
            "Network latency is high",
            "Server is under heavy load",
        ],
        suggestions=[
            "Increase timeout: yami --timeout 60 <command>",
            "Check server status and load",
            "yami doctor                         # Run diagnostics",
        ],
    ),
    ErrorCode.AUTH_FAILED: ErrorInfo(
        code=ErrorCode.AUTH_FAILED,
        title="Authentication Failed",
        causes=[
            "Token is invalid or expired",
            "Token format is incorrect",
            "Server requires authentication but no token provided",
        ],
        suggestions=[
            "Check token: echo $MILVUS_TOKEN",
            "Update profile: yami config profile add <name> --uri <uri> --token <token>",
            "Verify token format (should be user:password or API key)",
        ],
    ),
    ErrorCode.SERVER_UNREACHABLE: ErrorInfo(
        code=ErrorCode.SERVER_UNREACHABLE,
        title="Server Unreachable",
        causes=[
            "Server is down or not responding",
            "DNS resolution failed",
            "SSL/TLS certificate error",
        ],
        suggestions=[
            "Verify server URL is correct",
            "Check DNS resolution: nslookup <host>",
            "For HTTPS, verify certificate is valid",
        ],
    ),
    ErrorCode.PROFILE_NOT_FOUND: ErrorInfo(
        code=ErrorCode.PROFILE_NOT_FOUND,
        title="Profile Not Found",
        causes=[
            "Profile name is misspelled",
            "Profile was never created",
            "Profile was deleted",
        ],
        suggestions=[
            "yami config profile list            # List available profiles",
            "yami config profile add <name> --uri <uri>  # Create new profile",
        ],
    ),
    ErrorCode.CONFIG_INVALID: ErrorInfo(
        code=ErrorCode.CONFIG_INVALID,
        title="Invalid Configuration",
        causes=[
            "Config file has syntax errors",
            "Invalid TOML format",
            "Unknown configuration keys",
        ],
        suggestions=[
            "yami config init                    # Recreate default config",
            "Check config file: cat ~/.yami/config.toml",
        ],
    ),
    ErrorCode.CONFIG_MISSING: ErrorInfo(
        code=ErrorCode.CONFIG_MISSING,
        title="Configuration Missing",
        causes=[
            "Config directory does not exist",
            "Config file was deleted",
        ],
        suggestions=[
            "yami config init                    # Initialize configuration",
        ],
    ),
    ErrorCode.COLLECTION_NOT_FOUND: ErrorInfo(
        code=ErrorCode.COLLECTION_NOT_FOUND,
        title="Collection Not Found",
        causes=[
            "Collection name is misspelled",
            "Collection was dropped",
            "Using wrong database",
        ],
        suggestions=[
            "yami collection list                # List available collections",
            "yami --db <name> collection list    # Check in specific database",
        ],
    ),
    ErrorCode.SCHEMA_INVALID: ErrorInfo(
        code=ErrorCode.SCHEMA_INVALID,
        title="Invalid Schema",
        causes=[
            "Field definition syntax error",
            "Unsupported field type",
            "Missing required field attributes",
        ],
        suggestions=[
            "yami collection create --field-help # Show field DSL syntax",
            "Check documentation for valid field types",
        ],
    ),
    ErrorCode.FIELD_NOT_FOUND: ErrorInfo(
        code=ErrorCode.FIELD_NOT_FOUND,
        title="Field Not Found",
        causes=[
            "Field name is misspelled",
            "Field does not exist in collection schema",
        ],
        suggestions=[
            "yami collection describe <name>     # Show collection schema",
        ],
    ),
    ErrorCode.VECTOR_DIMENSION_MISMATCH: ErrorInfo(
        code=ErrorCode.VECTOR_DIMENSION_MISMATCH,
        title="Vector Dimension Mismatch",
        causes=[
            "Input vector dimension differs from schema",
            "Wrong embedding model used",
        ],
        suggestions=[
            "yami collection describe <name>     # Check vector dimension in schema",
            "Verify your embedding model output dimension",
        ],
    ),
    ErrorCode.DATA_INVALID: ErrorInfo(
        code=ErrorCode.DATA_INVALID,
        title="Invalid Data",
        causes=[
            "Data format is incorrect",
            "Required fields are missing",
            "Data file cannot be parsed",
        ],
        suggestions=[
            "Check data file format (JSON, Parquet)",
            "Verify all required fields are present",
        ],
    ),
    ErrorCode.DATA_TYPE_MISMATCH: ErrorInfo(
        code=ErrorCode.DATA_TYPE_MISMATCH,
        title="Data Type Mismatch",
        causes=[
            "Field value type does not match schema",
            "String provided for numeric field",
            "Vector contains non-numeric values",
        ],
        suggestions=[
            "yami collection describe <name>     # Check field types",
            "Ensure data types match schema definition",
        ],
    ),
    ErrorCode.PRIMARY_KEY_DUPLICATE: ErrorInfo(
        code=ErrorCode.PRIMARY_KEY_DUPLICATE,
        title="Duplicate Primary Key",
        causes=[
            "Inserting data with existing primary key",
            "Data contains duplicate IDs",
        ],
        suggestions=[
            "Use upsert instead: yami data upsert <collection> ...",
            "Remove duplicates from input data",
        ],
    ),
    ErrorCode.OPERATION_FAILED: ErrorInfo(
        code=ErrorCode.OPERATION_FAILED,
        title="Operation Failed",
        causes=[
            "Server returned an error",
            "Operation is not supported",
        ],
        suggestions=[
            "yami --debug <command>              # Get detailed error info",
            "Check Milvus server logs",
        ],
    ),
    ErrorCode.PERMISSION_DENIED: ErrorInfo(
        code=ErrorCode.PERMISSION_DENIED,
        title="Permission Denied",
        causes=[
            "User lacks required privileges",
            "Role does not have permission for this operation",
        ],
        suggestions=[
            "yami user describe <username>       # Check user roles",
            "Contact admin to grant required privileges",
        ],
    ),
    ErrorCode.RESOURCE_NOT_LOADED: ErrorInfo(
        code=ErrorCode.RESOURCE_NOT_LOADED,
        title="Resource Not Loaded",
        causes=[
            "Collection is not loaded into memory",
            "Partition is not loaded",
        ],
        suggestions=[
            "yami load collection <name>         # Load collection",
            "yami load state <name>              # Check load state",
        ],
    ),
    ErrorCode.UNKNOWN: ErrorInfo(
        code=ErrorCode.UNKNOWN,
        title="Unknown Error",
        causes=[
            "An unexpected error occurred",
        ],
        suggestions=[
            "yami --debug <command>              # Get detailed error info",
            "yami doctor                         # Run diagnostics",
            "Report issue: https://github.com/mmga-lab/yami-cli/issues",
        ],
    ),
}


def get_error_info(code: ErrorCode) -> ErrorInfo:
    """Get error information by code."""
    return ERROR_CATALOG.get(code, ERROR_CATALOG[ErrorCode.UNKNOWN])


def classify_connection_error(error_message: str) -> ErrorCode:
    """Classify a connection error based on error message."""
    msg = error_message.lower()

    if "timeout" in msg or "timed out" in msg:
        return ErrorCode.CONNECTION_TIMEOUT
    if "auth" in msg or "unauthorized" in msg or "permission" in msg:
        return ErrorCode.AUTH_FAILED
    if "dns" in msg or "resolve" in msg or "unreachable" in msg:
        return ErrorCode.SERVER_UNREACHABLE
    if "connection" in msg or "connect" in msg or "refused" in msg:
        return ErrorCode.CONNECTION_FAILED

    return ErrorCode.CONNECTION_FAILED


def classify_milvus_error(error_message: str) -> ErrorCode:
    """Classify a Milvus error based on error message."""
    msg = error_message.lower()

    if "collection" in msg and ("not found" in msg or "not exist" in msg):
        return ErrorCode.COLLECTION_NOT_FOUND
    if "field" in msg and ("not found" in msg or "not exist" in msg):
        return ErrorCode.FIELD_NOT_FOUND
    if "dimension" in msg or "dim" in msg:
        return ErrorCode.VECTOR_DIMENSION_MISMATCH
    if "type" in msg and ("mismatch" in msg or "invalid" in msg):
        return ErrorCode.DATA_TYPE_MISMATCH
    if "duplicate" in msg or "primary key" in msg:
        return ErrorCode.PRIMARY_KEY_DUPLICATE
    if "permission" in msg or "denied" in msg or "privilege" in msg:
        return ErrorCode.PERMISSION_DENIED
    if "not loaded" in msg or "load" in msg and "first" in msg:
        return ErrorCode.RESOURCE_NOT_LOADED
    if "schema" in msg and ("invalid" in msg or "error" in msg):
        return ErrorCode.SCHEMA_INVALID

    return ErrorCode.OPERATION_FAILED
