"""Partition management commands."""

from __future__ import annotations

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_partitions(
    collection: str = typer.Argument(..., help="Collection name"),
) -> None:
    """List all partitions in a collection."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        partitions = client.list_partitions(collection)
        format_output(partitions, ctx.output, title=f"Partitions: {collection}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    collection: str = typer.Argument(..., help="Collection name"),
    name: str = typer.Argument(..., help="Partition name"),
) -> None:
    """Create a partition."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.create_partition(collection, name)
        print_success(f"Partition '{name}' created in collection '{collection}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def drop(
    collection: str = typer.Argument(..., help="Collection name"),
    name: str = typer.Argument(..., help="Partition name"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Drop a partition."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to drop partition '{name}'?")
        if not confirm:
            raise typer.Abort()

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_partition(collection, name)
        print_success(f"Partition '{name}' dropped from collection '{collection}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def has(
    collection: str = typer.Argument(..., help="Collection name"),
    name: str = typer.Argument(..., help="Partition name"),
) -> None:
    """Check if a partition exists."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        exists = client.has_partition(collection, name)
        if exists:
            print_success(f"Partition '{name}' exists in collection '{collection}'")
        else:
            typer.echo(f"Partition '{name}' does not exist in collection '{collection}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def stats(
    collection: str = typer.Argument(..., help="Collection name"),
    name: str = typer.Argument(..., help="Partition name"),
) -> None:
    """Get partition statistics."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        stats_data = client.get_partition_stats(collection, name)
        format_output(stats_data, ctx.output, title=f"Partition Stats: {name}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
