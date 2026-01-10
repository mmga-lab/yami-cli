"""Collection management commands."""

from __future__ import annotations

import json
from typing import Annotated, Optional

import typer

from yami.core.context import get_context
from yami.core.schema import (
    SchemaParseError,
    build_index_params,
    build_schema,
    format_field_help,
    parse_field,
    parse_fields,
)
from yami.output.formatter import format_output, print_error, print_info, print_success

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_collections() -> None:
    """List all collections in the current database."""
    ctx = get_context()
    client = ctx.get_client()

    collections = client.list_collections()
    format_output(collections, ctx.output, title="Collections")


@app.command()
def describe(
    name: str = typer.Argument(..., help="Collection name"),
) -> None:
    """Describe a collection's schema and properties."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        info = client.describe_collection(name)
        format_output(info, ctx.output, title=f"Collection: {name}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(None, help="Collection name"),
    fields: Annotated[
        Optional[list[str]],
        typer.Option(
            "--field",
            "-f",
            help="Field definition (can be repeated). Format: name:type[:param][:modifier...]",
        ),
    ] = None,
    dimension: Optional[int] = typer.Option(
        None,
        "--dim",
        "-d",
        help="Vector dimension (quick create: id + vector only)",
    ),
    metric_type: str = typer.Option(
        "COSINE",
        "--metric",
        "-m",
        help="Metric type for quick create: COSINE, L2, IP",
    ),
    auto_id: bool = typer.Option(
        False,
        "--auto-id",
        help="Enable auto ID generation (quick create mode)",
    ),
    no_dynamic: bool = typer.Option(
        False,
        "--no-dynamic",
        help="Disable dynamic fields",
    ),
    show_help: bool = typer.Option(
        False,
        "--field-help",
        help="Show field DSL syntax help",
    ),
) -> None:
    """Create a new collection.

    \b
    Quick create (--dim):
      yami collection create my_col --dim 768
      Creates: id (int64, pk) + vector (float_vector)

    \b
    Field DSL (--field):
      yami collection create my_col \\
        --field "id:int64:pk:auto" \\
        --field "title:varchar:512" \\
        --field "embedding:float_vector:768:COSINE"

    \b
    Use --field-help to see full DSL syntax.
    """
    # Show field help if requested
    if show_help:
        print_info(format_field_help())
        raise typer.Exit()

    # Validate name is provided
    if not name:
        print_error("Collection name is required")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        if fields:
            # DSL mode: parse field definitions
            try:
                specs = parse_fields(fields)
            except SchemaParseError as e:
                print_error(str(e))
                print_info("Use --field-help to see field DSL syntax")
                raise typer.Exit(1)

            # Build schema and index params
            schema = build_schema(specs, enable_dynamic=not no_dynamic)
            index_params = build_index_params(specs)

            client.create_collection(
                collection_name=name,
                schema=schema,
                index_params=index_params,
            )
            print_success(f"Collection '{name}' created with {len(specs)} fields")

        elif dimension:
            # Quick create mode
            client.create_collection(
                collection_name=name,
                dimension=dimension,
                metric_type=metric_type,
                auto_id=auto_id,
            )
            print_success(f"Collection '{name}' created (quick mode, dim={dimension})")

        else:
            print_error("Either --field or --dim is required")
            print_info("Examples:")
            print_info("  Quick:  yami collection create my_col --dim 768")
            print_info("  DSL:    yami collection create my_col -f 'id:int64:pk' -f 'vec:float_vector:768'")
            raise typer.Exit(1)

    except SchemaParseError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def drop(
    name: str = typer.Argument(..., help="Collection name"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Drop a collection."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to drop collection '{name}'?")
        if not confirm:
            raise typer.Abort()

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_collection(name)
        print_success(f"Collection '{name}' dropped successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def has(
    name: str = typer.Argument(..., help="Collection name"),
) -> None:
    """Check if a collection exists."""
    ctx = get_context()
    client = ctx.get_client()

    exists = client.has_collection(name)
    if exists:
        print_success(f"Collection '{name}' exists")
    else:
        typer.echo(f"Collection '{name}' does not exist")


@app.command()
def rename(
    old_name: str = typer.Argument(..., help="Current collection name"),
    new_name: str = typer.Argument(..., help="New collection name"),
    target_db: Optional[str] = typer.Option(
        None,
        "--target-db",
        help="Target database (for cross-database rename)",
    ),
) -> None:
    """Rename a collection."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.rename_collection(old_name, new_name, target_db=target_db or "")
        print_success(f"Collection renamed from '{old_name}' to '{new_name}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def stats(
    name: str = typer.Argument(..., help="Collection name"),
) -> None:
    """Get collection statistics."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        stats_data = client.get_collection_stats(name)
        format_output(stats_data, ctx.output, title=f"Stats: {name}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("add-field")
def add_field(
    collection: str = typer.Argument(..., help="Collection name"),
    field: str = typer.Argument(
        ...,
        help="Field definition (e.g., 'score:int64', 'tags:array:varchar:100')",
    ),
    default: Optional[str] = typer.Option(
        None,
        "--default",
        "-d",
        help="Default value for the field (JSON format for complex types)",
    ),
) -> None:
    """Add a new field to an existing collection.

    \b
    Requires: Milvus 2.6.0 or later

    \b
    Field syntax: name:type[:param][:modifier]

    \b
    Note: Added fields MUST include :nullable modifier.

    \b
    Examples:
      # Add nullable integer field
      yami collection add-field my_col "score:int64:nullable"

      # Add nullable field with default value
      yami collection add-field my_col "status:varchar:64:nullable" --default '"active"'

      # Add nullable array field
      yami collection add-field my_col "tags:array:varchar:100:nullable"

      # Add nullable vector field
      yami collection add-field my_col "extra_vec:float_vector:128:nullable"
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        # Parse field spec
        spec = parse_field(field)

        # Build kwargs
        kwargs = {}

        if spec.max_length is not None:
            kwargs["max_length"] = spec.max_length
        if spec.dim is not None:
            kwargs["dim"] = spec.dim
        if spec.element_type is not None:
            kwargs["element_type"] = spec.element_type
        if spec.max_capacity is not None:
            kwargs["max_capacity"] = spec.max_capacity
        if spec.nullable:
            kwargs["nullable"] = True

        # Parse default value
        if default is not None:
            try:
                kwargs["default_value"] = json.loads(default)
            except json.JSONDecodeError:
                # Try as raw string
                kwargs["default_value"] = default

        # Add field
        client.add_collection_field(
            collection_name=collection,
            field_name=spec.name,
            data_type=spec.data_type,
            **kwargs,
        )

        print_success(f"Added field '{spec.name}' to collection '{collection}'")

    except SchemaParseError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
