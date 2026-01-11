"""Tests for schema DSL parser."""

import pytest
from pymilvus import DataType

from yami.core.schema import parse_field, parse_fields, SchemaParseError, build_schema, TYPE_MAP


class TestAllDataTypes:
    """Test all supported data types from pymilvus."""

    # ========== Scalar Types ==========

    def test_bool(self):
        spec = parse_field("flag:bool")
        assert spec.data_type == DataType.BOOL

    def test_int8(self):
        spec = parse_field("tiny:int8")
        assert spec.data_type == DataType.INT8

    def test_int16(self):
        spec = parse_field("small:int16")
        assert spec.data_type == DataType.INT16

    def test_int32(self):
        spec = parse_field("num:int32")
        assert spec.data_type == DataType.INT32

    def test_int64(self):
        spec = parse_field("id:int64")
        assert spec.data_type == DataType.INT64

    def test_float(self):
        spec = parse_field("score:float")
        assert spec.data_type == DataType.FLOAT

    def test_double(self):
        spec = parse_field("precise:double")
        assert spec.data_type == DataType.DOUBLE

    def test_varchar(self):
        spec = parse_field("name:varchar:256")
        assert spec.data_type == DataType.VARCHAR
        assert spec.max_length == 256

    def test_string_alias(self):
        """Test 'string' as alias for varchar."""
        spec = parse_field("name:string:256")
        assert spec.data_type == DataType.VARCHAR
        assert spec.max_length == 256

    def test_json(self):
        spec = parse_field("meta:json")
        assert spec.data_type == DataType.JSON

    # ========== Vector Types ==========

    def test_float_vector(self):
        spec = parse_field("vec:float_vector:128")
        assert spec.data_type == DataType.FLOAT_VECTOR
        assert spec.dim == 128
        assert spec.metric_type == "COSINE"

    def test_binary_vector(self):
        spec = parse_field("vec:binary_vector:128")
        assert spec.data_type == DataType.BINARY_VECTOR
        assert spec.dim == 128

    def test_float16_vector(self):
        spec = parse_field("vec:float16_vector:128")
        assert spec.data_type == DataType.FLOAT16_VECTOR
        assert spec.dim == 128

    def test_bfloat16_vector(self):
        spec = parse_field("vec:bfloat16_vector:128")
        assert spec.data_type == DataType.BFLOAT16_VECTOR
        assert spec.dim == 128

    def test_sparse_vector(self):
        spec = parse_field("vec:sparse_vector")
        assert spec.data_type == DataType.SPARSE_FLOAT_VECTOR

    def test_sparse_float_vector_alias(self):
        """Test 'sparse_float_vector' as alias."""
        spec = parse_field("vec:sparse_float_vector")
        assert spec.data_type == DataType.SPARSE_FLOAT_VECTOR

    # ========== Vector Metric Types ==========

    @pytest.mark.parametrize("metric", ["COSINE", "L2", "IP"])
    def test_float_vector_metrics(self, metric):
        spec = parse_field(f"vec:float_vector:128:{metric}")
        assert spec.metric_type == metric

    @pytest.mark.parametrize("metric", ["HAMMING", "JACCARD"])
    def test_binary_vector_metrics(self, metric):
        spec = parse_field(f"vec:binary_vector:128:{metric}")
        assert spec.metric_type == metric

    # ========== TYPE_MAP Coverage ==========

    def test_type_map_completeness(self):
        """Verify all TYPE_MAP entries can be parsed."""
        for type_name, expected_type in TYPE_MAP.items():
            if type_name == "array":
                # array needs element type
                spec = parse_field(f"field:array:int64")
            elif type_name in ("varchar", "string"):
                spec = parse_field(f"field:{type_name}:256")
            elif type_name in ("float_vector", "binary_vector", "float16_vector", "bfloat16_vector"):
                spec = parse_field(f"field:{type_name}:128")
            elif type_name in ("sparse_vector", "sparse_float_vector"):
                spec = parse_field(f"field:{type_name}")
            else:
                spec = parse_field(f"field:{type_name}")
            assert spec.data_type == expected_type, f"Failed for {type_name}"


class TestParseField:
    """Test parse_field function."""

    def test_simple_int64(self):
        spec = parse_field("id:int64")
        assert spec.name == "id"
        assert spec.data_type == DataType.INT64
        assert not spec.is_primary
        assert not spec.auto_id

    def test_primary_key(self):
        spec = parse_field("id:int64:pk")
        assert spec.is_primary
        assert not spec.auto_id

    def test_auto_id(self):
        spec = parse_field("id:int64:pk:auto")
        assert spec.is_primary
        assert spec.auto_id

    def test_varchar_with_length(self):
        spec = parse_field("title:varchar:512")
        assert spec.data_type == DataType.VARCHAR
        assert spec.max_length == 512

    def test_varchar_default_length(self):
        spec = parse_field("title:varchar")
        assert spec.max_length == 65535

    def test_float_vector(self):
        spec = parse_field("embedding:float_vector:768")
        assert spec.data_type == DataType.FLOAT_VECTOR
        assert spec.dim == 768
        assert spec.metric_type == "COSINE"

    def test_float_vector_with_metric(self):
        spec = parse_field("embedding:float_vector:128:L2")
        assert spec.dim == 128
        assert spec.metric_type == "L2"

    def test_nullable(self):
        spec = parse_field("content:varchar:1024:nullable")
        assert spec.nullable

    # ========== Array field tests ==========

    @pytest.mark.parametrize("elem_type,expected", [
        ("bool", DataType.BOOL),
        ("int8", DataType.INT8),
        ("int16", DataType.INT16),
        ("int32", DataType.INT32),
        ("int64", DataType.INT64),
        ("float", DataType.FLOAT),
        ("double", DataType.DOUBLE),
    ])
    def test_array_scalar_types(self, elem_type, expected):
        """Test array with all scalar element types."""
        spec = parse_field(f"arr:array:{elem_type}:100")
        assert spec.data_type == DataType.ARRAY
        assert spec.element_type == expected
        assert spec.max_capacity == 100
        assert spec.max_length is None

    def test_array_int64(self):
        """Test array of int64."""
        spec = parse_field("scores:array:int64:100")
        assert spec.data_type == DataType.ARRAY
        assert spec.element_type == DataType.INT64
        assert spec.max_capacity == 100
        assert spec.max_length is None

    def test_array_int64_default_capacity(self):
        """Test array of int64 with default capacity."""
        spec = parse_field("scores:array:int64")
        assert spec.element_type == DataType.INT64
        assert spec.max_capacity == 4096

    def test_array_float(self):
        """Test array of float."""
        spec = parse_field("values:array:float:50")
        assert spec.element_type == DataType.FLOAT
        assert spec.max_capacity == 50

    def test_array_varchar_with_length_and_capacity(self):
        """Test array of varchar with max_length and max_capacity."""
        spec = parse_field("tags:array:varchar:64:100")
        assert spec.data_type == DataType.ARRAY
        assert spec.element_type == DataType.VARCHAR
        assert spec.max_length == 64
        assert spec.max_capacity == 100

    def test_array_varchar_with_length_only(self):
        """Test array of varchar with max_length only (default capacity)."""
        spec = parse_field("tags:array:varchar:128")
        assert spec.element_type == DataType.VARCHAR
        assert spec.max_length == 128
        assert spec.max_capacity == 4096

    def test_array_varchar_default_all(self):
        """Test array of varchar with all defaults."""
        spec = parse_field("tags:array:varchar")
        assert spec.element_type == DataType.VARCHAR
        assert spec.max_length == 65535
        assert spec.max_capacity == 4096

    def test_array_string_alias(self):
        """Test array with 'string' alias for varchar."""
        spec = parse_field("tags:array:string:64:100")
        assert spec.element_type == DataType.VARCHAR
        assert spec.max_length == 64
        assert spec.max_capacity == 100

    def test_array_varchar_nullable(self):
        """Test nullable array of varchar."""
        spec = parse_field("tags:array:varchar:64:100:nullable")
        assert spec.element_type == DataType.VARCHAR
        assert spec.max_length == 64
        assert spec.max_capacity == 100
        assert spec.nullable

    # ========== Struct field tests ==========

    def test_struct_basic(self):
        """Test basic struct with two fields."""
        spec = parse_field("info:struct(name:varchar:64,age:int32):100")
        assert spec.data_type == DataType.ARRAY  # struct uses ARRAY type internally
        assert spec.struct_fields is not None
        assert len(spec.struct_fields) == 2
        assert spec.max_capacity == 100

        # Check sub-fields
        name_field = spec.struct_fields[0]
        assert name_field.name == "name"
        assert name_field.data_type == DataType.VARCHAR
        assert name_field.max_length == 64

        age_field = spec.struct_fields[1]
        assert age_field.name == "age"
        assert age_field.data_type == DataType.INT32

    def test_struct_default_capacity(self):
        """Test struct with default max_capacity."""
        spec = parse_field("info:struct(name:varchar:64,age:int32)")
        assert spec.max_capacity == 4096

    def test_struct_single_field(self):
        """Test struct with single field."""
        spec = parse_field("data:struct(value:float):50")
        assert len(spec.struct_fields) == 1
        assert spec.struct_fields[0].name == "value"
        assert spec.struct_fields[0].data_type == DataType.FLOAT

    def test_struct_with_all_scalar_types(self):
        """Test struct containing various scalar types."""
        spec = parse_field("record:struct(a:bool,b:int8,c:int16,d:int32,e:int64,f:float,g:double):10")
        assert len(spec.struct_fields) == 7
        expected_types = [
            DataType.BOOL, DataType.INT8, DataType.INT16, DataType.INT32,
            DataType.INT64, DataType.FLOAT, DataType.DOUBLE
        ]
        for i, expected in enumerate(expected_types):
            assert spec.struct_fields[i].data_type == expected

    def test_struct_with_array_field(self):
        """Test struct containing array field."""
        spec = parse_field("data:struct(scores:array:int64:50,name:varchar:64):100")
        assert len(spec.struct_fields) == 2

        scores_field = spec.struct_fields[0]
        assert scores_field.name == "scores"
        assert scores_field.data_type == DataType.ARRAY
        assert scores_field.element_type == DataType.INT64
        assert scores_field.max_capacity == 50

    def test_struct_with_json_field(self):
        """Test struct containing JSON field."""
        spec = parse_field("meta:struct(config:json,name:varchar:32):20")
        assert len(spec.struct_fields) == 2
        assert spec.struct_fields[0].data_type == DataType.JSON

    def test_struct_error_empty_fields(self):
        """Test struct with empty fields raises error."""
        with pytest.raises(SchemaParseError, match="must have at least one field"):
            parse_field("info:struct():100")

    def test_struct_error_nested_struct(self):
        """Test nested struct raises error."""
        # Nested struct syntax causes parsing issues due to parentheses
        with pytest.raises(SchemaParseError, match="Unknown type"):
            parse_field("info:struct(inner:struct(a:int32)):100")

    def test_struct_error_vector_field(self):
        """Test struct with vector field raises error."""
        with pytest.raises(SchemaParseError, match="not supported in struct"):
            parse_field("info:struct(vec:float_vector:128):100")

    def test_struct_error_pk_modifier(self):
        """Test struct sub-field with pk modifier raises error."""
        with pytest.raises(SchemaParseError, match="not allowed"):
            parse_field("info:struct(id:int64:pk):100")

    # ========== Error cases ==========

    def test_error_empty_name(self):
        with pytest.raises(SchemaParseError, match="Field name cannot be empty"):
            parse_field(":int64")

    def test_error_unknown_type(self):
        with pytest.raises(SchemaParseError, match="Unknown type"):
            parse_field("id:unknown")

    def test_error_vector_no_dim(self):
        with pytest.raises(SchemaParseError, match="requires dimension"):
            parse_field("vec:float_vector")

    def test_error_array_no_element_type(self):
        with pytest.raises(SchemaParseError, match="requires element type"):
            parse_field("arr:array")

    def test_error_auto_without_pk(self):
        with pytest.raises(SchemaParseError, match="'auto' modifier requires 'pk'"):
            parse_field("id:int64:auto")


class TestParseFields:
    """Test parse_fields function."""

    def test_simple_schema(self):
        specs = parse_fields([
            "id:int64:pk",
            "vec:float_vector:128",
        ])
        assert len(specs) == 2
        assert specs[0].is_primary

    def test_error_no_pk(self):
        with pytest.raises(SchemaParseError, match="must be marked as primary key"):
            parse_fields(["id:int64", "vec:float_vector:128"])

    def test_error_multiple_pk(self):
        with pytest.raises(SchemaParseError, match="Only one field"):
            parse_fields(["id:int64:pk", "name:varchar:64:pk"])


class TestBuildSchema:
    """Test build_schema function."""

    def test_build_simple_schema(self):
        specs = parse_fields([
            "id:int64:pk",
            "vec:float_vector:128",
        ])
        schema = build_schema(specs)
        assert len(schema.fields) == 2

    def test_build_schema_with_array_varchar(self):
        """Test building schema with array<varchar> field."""
        specs = parse_fields([
            "id:int64:pk",
            "vec:float_vector:128",
            "tags:array:varchar:64:100",
        ])
        schema = build_schema(specs)
        assert len(schema.fields) == 3

        # Find the tags field
        tags_field = next(f for f in schema.fields if f.name == "tags")
        assert tags_field.dtype == DataType.ARRAY
        assert tags_field.element_type == DataType.VARCHAR
        # max_length and max_capacity should be in the params
        assert tags_field.params.get("max_length") == 64
        assert tags_field.params.get("max_capacity") == 100

    def test_build_schema_with_array_int64(self):
        """Test building schema with array<int64> field."""
        specs = parse_fields([
            "id:int64:pk",
            "vec:float_vector:128",
            "scores:array:int64:50",
        ])
        schema = build_schema(specs)

        scores_field = next(f for f in schema.fields if f.name == "scores")
        assert scores_field.dtype == DataType.ARRAY
        assert scores_field.element_type == DataType.INT64
        assert scores_field.params.get("max_capacity") == 50
        # int64 array should not have max_length
        assert scores_field.params.get("max_length") is None

    def test_build_schema_with_struct(self):
        """Test building schema with struct field."""
        specs = parse_fields([
            "id:int64:pk",
            "vec:float_vector:128",
            "info:struct(name:varchar:64,age:int32):100",
        ])
        schema = build_schema(specs)

        # Regular fields should be 2 (id and vec)
        assert len(schema.fields) == 2

        # Struct fields should be 1
        assert len(schema.struct_fields) == 1

        # Check the struct field
        info_struct = schema.struct_fields[0]
        assert info_struct.name == "info"
        assert info_struct.max_capacity == 100
        assert len(info_struct._fields) == 2

        # Check sub-fields
        name_field = info_struct._fields[0]
        assert name_field.name == "name"
        assert name_field.dtype == DataType.VARCHAR
        assert name_field.params.get("max_length") == 64

        age_field = info_struct._fields[1]
        assert age_field.name == "age"
        assert age_field.dtype == DataType.INT32
