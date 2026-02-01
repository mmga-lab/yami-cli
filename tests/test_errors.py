"""Tests for error handling system."""

from yami.core.error_catalog import (
    ERROR_CATALOG,
    ErrorCode,
    ErrorInfo,
    classify_connection_error,
    classify_milvus_error,
    get_error_info,
)
from yami.exceptions import (
    AuthError,
    CollectionError,
    ConnectionError,
    DataError,
    OperationError,
    ProfileNotFoundError,
    SchemaError,
    YamiError,
)


class TestErrorCode:
    """Test ErrorCode enum."""

    def test_error_codes_are_strings(self):
        """Error codes should be string values."""
        assert ErrorCode.CONNECTION_FAILED.value == "E001"
        assert ErrorCode.AUTH_FAILED.value == "E003"
        assert ErrorCode.PROFILE_NOT_FOUND.value == "E010"

    def test_all_error_codes_in_catalog(self):
        """All error codes should have entries in the catalog."""
        for code in ErrorCode:
            assert code in ERROR_CATALOG, f"Missing catalog entry for {code}"


class TestErrorInfo:
    """Test ErrorInfo dataclass."""

    def test_error_info_structure(self):
        """ErrorInfo should have correct structure."""
        info = get_error_info(ErrorCode.CONNECTION_FAILED)
        assert isinstance(info, ErrorInfo)
        assert info.code == ErrorCode.CONNECTION_FAILED
        assert info.title == "Connection Failed"
        assert isinstance(info.causes, list)
        assert isinstance(info.suggestions, list)
        assert len(info.causes) > 0
        assert len(info.suggestions) > 0


class TestClassifyConnectionError:
    """Test connection error classification."""

    def test_timeout_error(self):
        assert classify_connection_error("Connection timed out") == ErrorCode.CONNECTION_TIMEOUT
        assert classify_connection_error("timeout error") == ErrorCode.CONNECTION_TIMEOUT

    def test_auth_error(self):
        assert classify_connection_error("unauthorized access") == ErrorCode.AUTH_FAILED
        assert classify_connection_error("authentication failed") == ErrorCode.AUTH_FAILED
        assert classify_connection_error("permission denied") == ErrorCode.AUTH_FAILED

    def test_unreachable_error(self):
        assert classify_connection_error("DNS resolution failed") == ErrorCode.SERVER_UNREACHABLE
        assert classify_connection_error("host unreachable") == ErrorCode.SERVER_UNREACHABLE

    def test_connection_refused(self):
        assert classify_connection_error("connection refused") == ErrorCode.CONNECTION_FAILED
        assert classify_connection_error("failed to connect") == ErrorCode.CONNECTION_FAILED

    def test_unknown_defaults_to_connection_failed(self):
        assert classify_connection_error("some random error") == ErrorCode.CONNECTION_FAILED


class TestClassifyMilvusError:
    """Test Milvus error classification."""

    def test_collection_not_found(self):
        assert classify_milvus_error("collection not found") == ErrorCode.COLLECTION_NOT_FOUND
        assert classify_milvus_error("collection does not exist") == ErrorCode.COLLECTION_NOT_FOUND

    def test_field_not_found(self):
        assert classify_milvus_error("field not found") == ErrorCode.FIELD_NOT_FOUND

    def test_dimension_mismatch(self):
        assert classify_milvus_error("dimension mismatch") == ErrorCode.VECTOR_DIMENSION_MISMATCH
        assert classify_milvus_error("vector dim error") == ErrorCode.VECTOR_DIMENSION_MISMATCH

    def test_type_mismatch(self):
        assert classify_milvus_error("type mismatch") == ErrorCode.DATA_TYPE_MISMATCH
        assert classify_milvus_error("invalid type") == ErrorCode.DATA_TYPE_MISMATCH

    def test_duplicate_key(self):
        assert classify_milvus_error("duplicate primary key") == ErrorCode.PRIMARY_KEY_DUPLICATE

    def test_permission_denied(self):
        assert classify_milvus_error("permission denied") == ErrorCode.PERMISSION_DENIED
        assert classify_milvus_error("privilege required") == ErrorCode.PERMISSION_DENIED

    def test_not_loaded(self):
        assert classify_milvus_error("collection not loaded") == ErrorCode.RESOURCE_NOT_LOADED
        assert classify_milvus_error("load collection first") == ErrorCode.RESOURCE_NOT_LOADED

    def test_schema_error(self):
        assert classify_milvus_error("schema invalid") == ErrorCode.SCHEMA_INVALID
        assert classify_milvus_error("schema error") == ErrorCode.SCHEMA_INVALID

    def test_unknown_defaults_to_operation_failed(self):
        assert classify_milvus_error("some random error") == ErrorCode.OPERATION_FAILED


class TestYamiError:
    """Test base YamiError exception."""

    def test_basic_error(self):
        err = YamiError("test message")
        assert err.message == "test message"
        assert str(err) == "test message"
        assert err.code == ErrorCode.UNKNOWN
        assert err.context == {}

    def test_error_with_code(self):
        err = YamiError("test", code=ErrorCode.CONNECTION_FAILED)
        assert err.code == ErrorCode.CONNECTION_FAILED

    def test_error_with_context(self):
        err = YamiError("test", context={"key": "value"})
        assert err.context == {"key": "value"}

    def test_with_context_method(self):
        err = YamiError("test").with_context(uri="http://localhost")
        assert err.context["uri"] == "http://localhost"


class TestConnectionError:
    """Test ConnectionError exception."""

    def test_auto_classification_connection_refused(self):
        err = ConnectionError("connection refused to server")
        assert err.code == ErrorCode.CONNECTION_FAILED

    def test_auto_classification_timeout(self):
        err = ConnectionError("connection timed out")
        assert err.code == ErrorCode.CONNECTION_TIMEOUT

    def test_auto_classification_auth(self):
        err = ConnectionError("unauthorized")
        assert err.code == ErrorCode.AUTH_FAILED

    def test_uri_in_context(self):
        err = ConnectionError("failed", uri="http://localhost:19530")
        assert err.context["uri"] == "http://localhost:19530"

    def test_explicit_code_overrides_auto(self):
        err = ConnectionError("test", code=ErrorCode.SERVER_UNREACHABLE)
        assert err.code == ErrorCode.SERVER_UNREACHABLE


class TestProfileNotFoundError:
    """Test ProfileNotFoundError exception."""

    def test_default_message(self):
        err = ProfileNotFoundError("myprofile")
        assert "myprofile" in err.message
        assert err.profile_name == "myprofile"

    def test_code_is_profile_not_found(self):
        err = ProfileNotFoundError("test")
        assert err.code == ErrorCode.PROFILE_NOT_FOUND

    def test_context_has_profile(self):
        err = ProfileNotFoundError("myprofile")
        assert err.context["profile"] == "myprofile"


class TestCollectionError:
    """Test CollectionError exception."""

    def test_auto_classification(self):
        err = CollectionError("collection not found")
        assert err.code == ErrorCode.COLLECTION_NOT_FOUND

    def test_collection_in_context(self):
        err = CollectionError("error", collection="my_collection")
        assert err.context["collection"] == "my_collection"


class TestSchemaError:
    """Test SchemaError exception."""

    def test_default_code(self):
        err = SchemaError("invalid schema")
        assert err.code == ErrorCode.SCHEMA_INVALID


class TestDataError:
    """Test DataError exception."""

    def test_auto_classification(self):
        err = DataError("type mismatch in field")
        assert err.code == ErrorCode.DATA_TYPE_MISMATCH


class TestAuthError:
    """Test AuthError exception."""

    def test_code_is_auth_failed(self):
        err = AuthError("authentication failed")
        assert err.code == ErrorCode.AUTH_FAILED


class TestOperationError:
    """Test OperationError exception."""

    def test_auto_classification(self):
        err = OperationError("permission denied")
        assert err.code == ErrorCode.PERMISSION_DENIED

    def test_default_code(self):
        err = OperationError("unknown error")
        assert err.code == ErrorCode.OPERATION_FAILED
