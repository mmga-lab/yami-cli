"""Index management commands."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success


def _parse_properties(props: list[str]) -> dict:
    """Parse property list in key=value format to dict."""
    result = {}
    for prop in props:
        if "=" not in prop:
            raise ValueError(f"Invalid property format: '{prop}'. Expected 'key=value'")
        key, value = prop.split("=", 1)
        try:
            result[key] = json.loads(value)
        except json.JSONDecodeError:
            result[key] = value
    return result

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_indexes(
    collection: str = typer.Argument(..., help="Collection name"),
    field: str | None = typer.Option(
        None,
        "--field",
        "-f",
        help="Field name to filter indexes",
    ),
) -> None:
    """List all indexes in a collection."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        indexes = client.list_indexes(collection, field_name=field)
        format_output(indexes, ctx.output, title=f"Indexes: {collection}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def describe(
    collection: str = typer.Argument(..., help="Collection name"),
    index_name: str = typer.Argument(..., help="Index name"),
) -> None:
    """Describe an index."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        info = client.describe_index(collection, index_name)
        format_output(info, ctx.output, title=f"Index: {index_name}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    collection: str = typer.Argument(..., help="Collection name"),
    field: str = typer.Argument(..., help="Field name to create index on"),
    index_type: str = typer.Option(
        "AUTOINDEX",
        "--type",
        "-t",
        help="Index type: AUTOINDEX, IVF_FLAT, IVF_SQ8, HNSW, etc.",
    ),
    metric_type: str = typer.Option(
        "COSINE",
        "--metric",
        "-m",
        help="Metric type: COSINE, L2, IP",
    ),
    index_name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="Index name (auto-generated if not specified)",
    ),
    nlist: int | None = typer.Option(
        None,
        "--nlist",
        help="Number of cluster units (for IVF indexes)",
    ),
    m: int | None = typer.Option(
        None,
        "--m",
        help="Maximum degree of the node (for HNSW)",
    ),
    ef_construction: int | None = typer.Option(
        None,
        "--ef-construction",
        help="ef parameter at construction time (for HNSW)",
    ),
) -> None:
    """Create an index on a field."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        # Build index params
        index_params = client.prepare_index_params()

        params = {"metric_type": metric_type, "index_type": index_type}

        if nlist:
            params["nlist"] = nlist
        if m:
            params["M"] = m
        if ef_construction:
            params["efConstruction"] = ef_construction

        index_params.add_index(
            field_name=field,
            index_name=index_name or "",
            **params,
        )

        client.create_index(collection, index_params)
        print_success(f"Index created on field '{field}' in collection '{collection}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def drop(
    collection: str = typer.Argument(..., help="Collection name"),
    index_name: str = typer.Argument(..., help="Index name to drop"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Drop an index."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to drop index '{index_name}'?")
        if not confirm:
            raise typer.Abort()

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_index(collection, index_name)
        print_success(f"Index '{index_name}' dropped from collection '{collection}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("alter-properties")
def alter_properties(
    collection: str = typer.Argument(..., help="Collection name"),
    index_name: str = typer.Argument(..., help="Index name"),
    props: Annotated[
        list[str] | None,
        typer.Option(
            "--prop",
            "-p",
            help="Property in key=value format (can be repeated)",
        ),
    ] = None,
) -> None:
    """Alter index properties.

    \b
    Examples:
      yami index alter-properties my_col my_index -p mmap.enabled=true
    """
    if not props:
        print_error("At least one --prop is required")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        properties = _parse_properties(props)
        client.alter_index_properties(
            collection_name=collection,
            index_name=index_name,
            properties=properties,
        )
        print_success(f"Updated index '{index_name}' properties in collection '{collection}'")
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("drop-properties")
def drop_properties(
    collection: str = typer.Argument(..., help="Collection name"),
    index_name: str = typer.Argument(..., help="Index name"),
    keys: Annotated[
        list[str] | None,
        typer.Option(
            "--key",
            "-k",
            help="Property key to drop (can be repeated)",
        ),
    ] = None,
) -> None:
    """Drop index properties.

    \b
    Examples:
      yami index drop-properties my_col my_index -k mmap.enabled
    """
    if not keys:
        print_error("At least one --key is required")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_index_properties(
            collection_name=collection,
            index_name=index_name,
            property_keys=keys,
        )
        print_success(f"Dropped {len(keys)} property(ies) from index '{index_name}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
