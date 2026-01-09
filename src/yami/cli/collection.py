"""Collection management commands."""

from __future__ import annotations

import json
from typing import Optional

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

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
    name: str = typer.Argument(..., help="Collection name"),
    dimension: Optional[int] = typer.Option(
        None,
        "--dim",
        "-d",
        help="Vector dimension (for quick create mode)",
    ),
    schema_file: Optional[str] = typer.Option(
        None,
        "--schema",
        "-s",
        help="Schema JSON file path (for custom schema)",
    ),
    metric_type: str = typer.Option(
        "COSINE",
        "--metric",
        "-m",
        help="Metric type: COSINE, L2, IP",
    ),
    auto_id: bool = typer.Option(
        False,
        "--auto-id",
        help="Enable auto ID generation",
    ),
    primary_field: str = typer.Option(
        "id",
        "--primary-field",
        help="Primary field name",
    ),
    vector_field: str = typer.Option(
        "vector",
        "--vector-field",
        help="Vector field name",
    ),
) -> None:
    """Create a new collection.

    Quick create mode (--dim): Creates a simple collection with id and vector fields.
    Custom schema mode (--schema): Creates a collection from a JSON schema file.
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        if schema_file:
            # Load schema from file
            with open(schema_file) as f:
                schema_data = json.load(f)
            # TODO: Parse and create collection from schema
            print_error("Schema file creation not yet implemented")
            raise typer.Exit(1)
        elif dimension:
            # Quick create mode
            client.create_collection(
                collection_name=name,
                dimension=dimension,
                metric_type=metric_type,
                auto_id=auto_id,
                primary_field_name=primary_field,
                vector_field_name=vector_field,
            )
            print_success(f"Collection '{name}' created successfully")
        else:
            print_error("Either --dim or --schema is required")
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
