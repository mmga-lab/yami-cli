"""Load/Release management commands."""

from __future__ import annotations

from typing import Optional

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


@app.command("collection")
def load_collection(
    name: str = typer.Argument(..., help="Collection name"),
) -> None:
    """Load a collection into memory."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.load_collection(name)
        print_success(f"Collection '{name}' loaded successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("partitions")
def load_partitions(
    collection: str = typer.Argument(..., help="Collection name"),
    partitions: str = typer.Argument(..., help="Comma-separated partition names"),
) -> None:
    """Load specific partitions into memory."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        partition_list = [p.strip() for p in partitions.split(",")]
        client.load_partitions(collection, partition_list)
        print_success(f"Partitions {partition_list} loaded successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def release(
    collection: str = typer.Argument(..., help="Collection name"),
    partitions: Optional[str] = typer.Option(
        None,
        "--partitions",
        "-p",
        help="Comma-separated partition names (if not specified, releases entire collection)",
    ),
) -> None:
    """Release a collection or partitions from memory."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        if partitions:
            partition_list = [p.strip() for p in partitions.split(",")]
            client.release_partitions(collection, partition_list)
            print_success(f"Partitions {partition_list} released from memory")
        else:
            client.release_collection(collection)
            print_success(f"Collection '{collection}' released from memory")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def state(
    collection: str = typer.Argument(..., help="Collection name"),
    partition: Optional[str] = typer.Option(
        None,
        "--partition",
        "-p",
        help="Partition name (optional)",
    ),
) -> None:
    """Get load state of a collection or partition."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        result = client.get_load_state(collection, partition_name=partition or "")
        format_output(result, ctx.output, title="Load State")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def refresh(
    collection: str = typer.Argument(..., help="Collection name"),
) -> None:
    """Refresh load state for a collection."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.refresh_load(collection)
        print_success(f"Load refreshed for collection '{collection}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
