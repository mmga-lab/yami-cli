"""Index management commands."""

from __future__ import annotations

from typing import Optional

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_indexes(
    collection: str = typer.Argument(..., help="Collection name"),
    field: Optional[str] = typer.Option(
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
    index_name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Index name (auto-generated if not specified)",
    ),
    nlist: Optional[int] = typer.Option(
        None,
        "--nlist",
        help="Number of cluster units (for IVF indexes)",
    ),
    m: Optional[int] = typer.Option(
        None,
        "--m",
        help="Maximum degree of the node (for HNSW)",
    ),
    ef_construction: Optional[int] = typer.Option(
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
