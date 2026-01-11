"""Schema DSL parser for collection creation.

DSL Syntax:
    field_name:type[:param][:modifier...]

Types:
    - int8, int16, int32, int64
    - float, double
    - bool
    - varchar:max_length (e.g., varchar:256)
    - json
    - array:element_type:max_capacity (e.g., array:int64:100)
    - array:varchar:max_length:max_capacity (e.g., array:varchar:64:100)
    - struct(field1:type1,field2:type2):max_capacity (e.g., struct(name:varchar:64,age:int32):100)
    - float_vector:dim (e.g., float_vector:768)
    - binary_vector:dim
    - float16_vector:dim
    - bfloat16_vector:dim
    - sparse_vector

Modifiers:
    - pk          Primary key
    - auto        Auto-generate ID
    - nullable    Allow null values
    - COSINE/L2/IP  Metric type for vector fields

Examples:
    id:int64:pk:auto
    title:varchar:512
    tags:array:varchar:64:100    # varchar array: max_length=64, max_capacity=100
    scores:array:float:50        # float array: max_capacity=50
    info:struct(name:varchar:64,age:int32):100  # struct array with max_capacity=100
    embedding:float_vector:768:COSINE
    content:varchar:65535:nullable
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pymilvus import DataType


# Type name to DataType mapping
TYPE_MAP = {
    "bool": DataType.BOOL,
    "int8": DataType.INT8,
    "int16": DataType.INT16,
    "int32": DataType.INT32,
    "int64": DataType.INT64,
    "float": DataType.FLOAT,
    "double": DataType.DOUBLE,
    "varchar": DataType.VARCHAR,
    "string": DataType.VARCHAR,  # alias
    "json": DataType.JSON,
    "array": DataType.ARRAY,
    "float_vector": DataType.FLOAT_VECTOR,
    "binary_vector": DataType.BINARY_VECTOR,
    "float16_vector": DataType.FLOAT16_VECTOR,
    "bfloat16_vector": DataType.BFLOAT16_VECTOR,
    "sparse_vector": DataType.SPARSE_FLOAT_VECTOR,
    "sparse_float_vector": DataType.SPARSE_FLOAT_VECTOR,
}

# Vector types that need dimension
VECTOR_TYPES = {
    DataType.FLOAT_VECTOR,
    DataType.BINARY_VECTOR,
    DataType.FLOAT16_VECTOR,
    DataType.BFLOAT16_VECTOR,
}

# Valid metric types
METRIC_TYPES = {"COSINE", "L2", "IP", "HAMMING", "JACCARD"}

# Modifiers
MODIFIERS = {"pk", "auto", "nullable"}


@dataclass
class FieldSpec:
    """Parsed field specification."""

    name: str
    data_type: DataType
    is_primary: bool = False
    auto_id: bool = False
    nullable: bool = False
    max_length: int | None = None  # for varchar
    dim: int | None = None  # for vectors
    metric_type: str | None = None  # for vectors
    element_type: DataType | None = None  # for array
    max_capacity: int | None = None  # for array and struct
    struct_fields: list["FieldSpec"] | None = None  # for struct
    extra_params: dict = field(default_factory=dict)


class SchemaParseError(Exception):
    """Error parsing schema DSL."""

    pass


def _parse_struct_inner_fields(inner_str: str) -> list[FieldSpec]:
    """Parse comma-separated fields inside struct(...).

    Handles nested colons in field definitions like 'name:varchar:64,age:int32'.

    Args:
        inner_str: The content inside struct(...), e.g., "name:varchar:64,age:int32"

    Returns:
        List of parsed FieldSpec for struct sub-fields
    """
    if not inner_str.strip():
        raise SchemaParseError("Struct must have at least one field")

    fields = []
    for field_def in inner_str.split(","):
        field_def = field_def.strip()
        if not field_def:
            continue
        # Parse each sub-field (without pk/auto modifiers)
        spec = _parse_struct_subfield(field_def)
        fields.append(spec)

    if not fields:
        raise SchemaParseError("Struct must have at least one field")

    return fields


def _parse_struct_subfield(field_str: str) -> FieldSpec:
    """Parse a single struct sub-field.

    Struct sub-fields cannot have pk, auto modifiers.
    Supported types: scalar types, varchar, array (no nested struct).

    Args:
        field_str: Field definition like "name:varchar:64" or "age:int32"

    Returns:
        Parsed FieldSpec
    """
    parts = [p.strip() for p in field_str.split(":")]

    if len(parts) < 2:
        raise SchemaParseError(
            f"Invalid struct field format: '{field_str}'. Expected 'name:type[:params...]'"
        )

    name = parts[0]
    type_name = parts[1].lower()

    if not name:
        raise SchemaParseError("Struct field name cannot be empty")

    if type_name not in TYPE_MAP:
        raise SchemaParseError(
            f"Unknown type '{type_name}' in struct field. Valid types: {', '.join(sorted(TYPE_MAP.keys()))}"
        )

    # Struct fields cannot contain nested structs
    if type_name == "struct":
        raise SchemaParseError("Nested struct is not supported")

    data_type = TYPE_MAP[type_name]
    spec = FieldSpec(name=name, data_type=data_type)

    remaining = parts[2:]

    # Handle type-specific parameters (similar to main parse_field)
    if data_type == DataType.VARCHAR:
        if remaining and remaining[0].isdigit():
            spec.max_length = int(remaining.pop(0))
        else:
            spec.max_length = 65535

    elif data_type in VECTOR_TYPES:
        raise SchemaParseError(f"Vector type '{type_name}' is not supported in struct fields")

    elif data_type == DataType.SPARSE_FLOAT_VECTOR:
        raise SchemaParseError("Sparse vector is not supported in struct fields")

    elif data_type == DataType.ARRAY:
        if not remaining:
            raise SchemaParseError(
                f"Array field '{name}' in struct requires element type"
            )
        elem_type_name = remaining.pop(0).lower()
        if elem_type_name not in TYPE_MAP:
            raise SchemaParseError(f"Unknown array element type '{elem_type_name}'")
        if elem_type_name == "struct":
            raise SchemaParseError("Array of struct is not supported in struct fields")
        spec.element_type = TYPE_MAP[elem_type_name]

        if spec.element_type == DataType.VARCHAR:
            if remaining and remaining[0].isdigit():
                spec.max_length = int(remaining.pop(0))
            else:
                spec.max_length = 65535
            if remaining and remaining[0].isdigit():
                spec.max_capacity = int(remaining.pop(0))
            else:
                spec.max_capacity = 4096
        else:
            if remaining and remaining[0].isdigit():
                spec.max_capacity = int(remaining.pop(0))
            else:
                spec.max_capacity = 4096

    # Struct sub-fields cannot have pk, auto, nullable modifiers
    for part in remaining:
        part_lower = part.lower()
        if part_lower in ("pk", "auto", "nullable"):
            raise SchemaParseError(
                f"Modifier '{part}' is not allowed in struct sub-fields"
            )
        else:
            raise SchemaParseError(f"Unknown modifier '{part}' in struct field")

    return spec


def _parse_struct_field(field_str: str) -> FieldSpec:
    """Parse a struct field with syntax: name:struct(field1:type1,field2:type2):max_capacity[:modifiers].

    Args:
        field_str: Struct field definition, e.g., "info:struct(name:varchar:64,age:int32):100"

    Returns:
        Parsed FieldSpec with struct_fields populated

    Raises:
        SchemaParseError: If the field string is invalid
    """
    import re

    # Pattern: name:struct(inner_fields):rest
    # We need to extract: name, inner content, and remaining params
    match = re.match(r"^([^:]+):struct\(([^)]*)\)(.*)$", field_str)
    if not match:
        raise SchemaParseError(
            f"Invalid struct format: '{field_str}'. "
            "Expected 'name:struct(field1:type1,field2:type2)[:max_capacity][:modifiers]'"
        )

    name = match.group(1).strip()
    inner_content = match.group(2).strip()
    rest = match.group(3).strip()

    if not name:
        raise SchemaParseError("Field name cannot be empty")

    # Parse inner struct fields
    struct_fields = _parse_struct_inner_fields(inner_content)

    # Create the FieldSpec for the struct
    # Note: pymilvus uses _ARRAY_OF_STRUCT for struct arrays
    spec = FieldSpec(
        name=name,
        data_type=DataType.ARRAY,  # Struct is stored as ARRAY type internally
        struct_fields=struct_fields,
    )

    # Parse remaining params (after the closing parenthesis)
    # rest could be ":100:nullable" or ":100" or ""
    if rest:
        if rest.startswith(":"):
            rest = rest[1:]  # Remove leading colon
        remaining = [p.strip() for p in rest.split(":") if p.strip()]

        # First number is max_capacity
        if remaining and remaining[0].isdigit():
            spec.max_capacity = int(remaining.pop(0))
        else:
            spec.max_capacity = 4096  # default

        # Parse modifiers
        for part in remaining:
            part_lower = part.lower()
            if part_lower == "nullable":
                spec.nullable = True
            elif part_lower in ("pk", "auto"):
                raise SchemaParseError(
                    f"Modifier '{part}' is not allowed on struct fields"
                )
            else:
                raise SchemaParseError(f"Unknown modifier '{part}'")
    else:
        spec.max_capacity = 4096  # default

    return spec


def parse_field(field_str: str) -> FieldSpec:
    """Parse a field DSL string into a FieldSpec.

    Args:
        field_str: Field definition string, e.g., "id:int64:pk:auto"
            For struct: "info:struct(name:varchar:64,age:int32):100"

    Returns:
        Parsed FieldSpec object

    Raises:
        SchemaParseError: If the field string is invalid
    """
    # Check for struct type with special syntax: name:struct(fields...):params
    if ":struct(" in field_str:
        return _parse_struct_field(field_str)

    parts = [p.strip() for p in field_str.split(":")]

    if len(parts) < 2:
        raise SchemaParseError(
            f"Invalid field format: '{field_str}'. Expected 'name:type[:params...]'"
        )

    name = parts[0]
    type_name = parts[1].lower()

    if not name:
        raise SchemaParseError("Field name cannot be empty")

    # Parse type
    if type_name not in TYPE_MAP:
        raise SchemaParseError(
            f"Unknown type '{type_name}'. Valid types: {', '.join(sorted(TYPE_MAP.keys()))}"
        )

    data_type = TYPE_MAP[type_name]
    spec = FieldSpec(name=name, data_type=data_type)

    # Remaining parts are params/modifiers
    remaining = parts[2:]

    # Handle type-specific parameters
    if data_type == DataType.VARCHAR:
        # varchar requires max_length
        if remaining and remaining[0].isdigit():
            spec.max_length = int(remaining.pop(0))
        else:
            spec.max_length = 65535  # default max length

    elif data_type in VECTOR_TYPES:
        # vector requires dimension
        if not remaining or not remaining[0].isdigit():
            raise SchemaParseError(f"Vector field '{name}' requires dimension, e.g., '{name}:{type_name}:768'")
        spec.dim = int(remaining.pop(0))

    elif data_type == DataType.ARRAY:
        # array requires element_type and optionally max_capacity
        # For varchar element type, max_length is also required
        # Syntax: array:elem_type:max_capacity or array:varchar:max_length:max_capacity
        if not remaining:
            raise SchemaParseError(
                f"Array field '{name}' requires element type, e.g., '{name}:array:int64:100'"
            )
        elem_type_name = remaining.pop(0).lower()
        if elem_type_name not in TYPE_MAP:
            raise SchemaParseError(f"Unknown array element type '{elem_type_name}'")
        spec.element_type = TYPE_MAP[elem_type_name]

        # For varchar element type, first number is max_length, second is max_capacity
        if spec.element_type == DataType.VARCHAR:
            if remaining and remaining[0].isdigit():
                spec.max_length = int(remaining.pop(0))
            else:
                spec.max_length = 65535  # default max_length for varchar elements

            if remaining and remaining[0].isdigit():
                spec.max_capacity = int(remaining.pop(0))
            else:
                spec.max_capacity = 4096  # default max_capacity
        else:
            # For other element types, number is max_capacity
            if remaining and remaining[0].isdigit():
                spec.max_capacity = int(remaining.pop(0))
            else:
                spec.max_capacity = 4096  # default

    # Parse modifiers
    for part in remaining:
        part_upper = part.upper()
        part_lower = part.lower()

        if part_lower == "pk":
            spec.is_primary = True
        elif part_lower == "auto":
            spec.auto_id = True
        elif part_lower == "nullable":
            spec.nullable = True
        elif part_upper in METRIC_TYPES:
            if data_type not in VECTOR_TYPES and data_type != DataType.SPARSE_FLOAT_VECTOR:
                raise SchemaParseError(
                    f"Metric type '{part}' can only be used with vector fields"
                )
            spec.metric_type = part_upper
        else:
            raise SchemaParseError(
                f"Unknown modifier '{part}'. Valid modifiers: pk, auto, nullable, "
                f"or metric types: {', '.join(METRIC_TYPES)}"
            )

    # Validation
    if spec.auto_id and not spec.is_primary:
        raise SchemaParseError(f"Field '{name}': 'auto' modifier requires 'pk' modifier")

    # Set default metric type for vectors
    if data_type in VECTOR_TYPES or data_type == DataType.SPARSE_FLOAT_VECTOR:
        if spec.metric_type is None:
            spec.metric_type = "COSINE" if data_type != DataType.SPARSE_FLOAT_VECTOR else "IP"

    return spec


def parse_fields(field_strs: list[str]) -> list[FieldSpec]:
    """Parse multiple field DSL strings.

    Args:
        field_strs: List of field definition strings

    Returns:
        List of parsed FieldSpec objects

    Raises:
        SchemaParseError: If any field string is invalid
    """
    specs = []
    primary_count = 0

    for field_str in field_strs:
        spec = parse_field(field_str)
        specs.append(spec)
        if spec.is_primary:
            primary_count += 1

    if primary_count == 0:
        raise SchemaParseError("At least one field must be marked as primary key (pk)")
    if primary_count > 1:
        raise SchemaParseError("Only one field can be marked as primary key")

    return specs


def _build_struct_field_schema(spec: FieldSpec) -> Any:
    """Build a StructFieldSchema from a FieldSpec with struct_fields.

    Args:
        spec: FieldSpec with struct_fields populated

    Returns:
        StructFieldSchema object
    """
    from pymilvus import FieldSchema
    from pymilvus.orm.schema import StructFieldSchema

    struct_schema = StructFieldSchema()
    struct_schema.name = spec.name
    struct_schema.max_capacity = spec.max_capacity or 4096

    # Add sub-fields to the struct
    for sub_spec in spec.struct_fields or []:
        sub_params: dict[str, Any] = {}

        if sub_spec.max_length is not None:
            sub_params["max_length"] = sub_spec.max_length
        if sub_spec.element_type is not None:
            sub_params["element_type"] = sub_spec.element_type
        if sub_spec.max_capacity is not None:
            sub_params["max_capacity"] = sub_spec.max_capacity

        sub_field = FieldSchema(
            name=sub_spec.name,
            dtype=sub_spec.data_type,
            **sub_params,
        )
        struct_schema._fields.append(sub_field)

    return struct_schema


def build_schema(specs: list[FieldSpec], enable_dynamic: bool = True) -> Any:
    """Build a Milvus CollectionSchema from parsed field specs.

    Args:
        specs: List of parsed FieldSpec objects
        enable_dynamic: Whether to enable dynamic fields

    Returns:
        MilvusClient-compatible schema
    """
    from pymilvus import CollectionSchema, FieldSchema

    fields = []
    struct_fields = []
    auto_id = False

    for spec in specs:
        # Handle struct fields separately
        if spec.struct_fields is not None:
            struct_schema = _build_struct_field_schema(spec)
            struct_fields.append(struct_schema)
            continue

        params: dict[str, Any] = {}

        if spec.max_length is not None:
            params["max_length"] = spec.max_length
        if spec.dim is not None:
            params["dim"] = spec.dim
        if spec.element_type is not None:
            params["element_type"] = spec.element_type
        if spec.max_capacity is not None:
            params["max_capacity"] = spec.max_capacity
        if spec.nullable:
            params["nullable"] = True

        field_schema = FieldSchema(
            name=spec.name,
            dtype=spec.data_type,
            is_primary=spec.is_primary,
            **params,
        )

        fields.append(field_schema)

        if spec.is_primary and spec.auto_id:
            auto_id = True

    schema = CollectionSchema(
        fields=fields,
        struct_fields=struct_fields if struct_fields else None,
        auto_id=auto_id,
        enable_dynamic_field=enable_dynamic,
    )

    return schema


def build_index_params(specs: list[FieldSpec]) -> Any:
    """Build index parameters for vector fields.

    Args:
        specs: List of parsed FieldSpec objects

    Returns:
        IndexParams object for MilvusClient
    """
    from pymilvus import MilvusClient

    index_params = MilvusClient.prepare_index_params()

    for spec in specs:
        if spec.data_type in VECTOR_TYPES or spec.data_type == DataType.SPARSE_FLOAT_VECTOR:
            index_params.add_index(
                field_name=spec.name,
                index_type="AUTOINDEX",
                metric_type=spec.metric_type or "COSINE",
            )

    return index_params


def format_field_help() -> str:
    """Return help text for field DSL syntax."""
    return """
Field DSL Syntax: name:type[:param][:modifier...]

Types:
  Scalar:     int8, int16, int32, int64, float, double, bool
  String:     varchar:max_len (e.g., varchar:256)
  JSON:       json
  Array:      array:elem_type:max_cap (e.g., array:int64:100)
              array:varchar:max_len:max_cap (e.g., array:varchar:64:100)
  Struct:     struct(field1:type1,field2:type2):max_cap
  Vector:     float_vector:dim, binary_vector:dim,
              float16_vector:dim, bfloat16_vector:dim, sparse_vector

Modifiers:
  pk          Primary key
  auto        Auto-generate ID (requires pk)
  nullable    Allow null values
  COSINE/L2/IP  Metric type for vector fields

Examples:
  id:int64:pk:auto              Auto-increment primary key
  title:varchar:512             String field, max 512 chars
  embedding:float_vector:768    768-dim vector with COSINE (default)
  vec:float_vector:128:L2       128-dim vector with L2 metric
  scores:array:int64:100        Array of int64, max 100 elements
  tags:array:varchar:64:100     Array of varchar (max 64 chars each), max 100 elements
  info:struct(name:varchar:64,age:int32):100  Struct array, max 100 elements
"""
