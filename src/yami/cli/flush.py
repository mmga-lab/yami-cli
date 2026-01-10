"""Flush and compaction commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("collection")
def flush_collection(
    name: str = typer.Argument(..., help="Collection name"),
) -> None:
    """Flush a collection to seal all segments.

    Inserts after flushing will be written into new segments.
    This ensures data is persisted to storage.
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.flush(name)
        print_success(f"Collection '{name}' flushed successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("all")
def flush_all() -> None:
    """Flush all collections in the database.

    This will seal all segments across all collections.
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.flush_all()
        print_success("All collections flushed successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


