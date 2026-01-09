"""Alias management commands."""

from __future__ import annotations

from typing import Optional

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_aliases(
    collection: Optional[str] = typer.Option(
        None,
        "--collection",
        "-c",
        help="Collection name (optional, list all aliases if not specified)",
    ),
) -> None:
    """List aliases."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        if collection:
            aliases = client.list_aliases(collection)
            format_output(aliases, ctx.output, title=f"Aliases for: {collection}")
        else:
            # List all collections and their aliases
            collections = client.list_collections()
            all_aliases = []
            for coll in collections:
                aliases = client.list_aliases(coll)
                for alias in aliases:
                    all_aliases.append({"collection": coll, "alias": alias})
            format_output(all_aliases, ctx.output, title="All Aliases")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def describe(
    alias: str = typer.Argument(..., help="Alias name"),
) -> None:
    """Describe an alias."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        info = client.describe_alias(alias)
        format_output(info, ctx.output, title=f"Alias: {alias}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    collection: str = typer.Argument(..., help="Collection name"),
    alias: str = typer.Argument(..., help="Alias name"),
) -> None:
    """Create an alias for a collection."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.create_alias(collection, alias)
        print_success(f"Alias '{alias}' created for collection '{collection}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def drop(
    alias: str = typer.Argument(..., help="Alias name"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Drop an alias."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to drop alias '{alias}'?")
        if not confirm:
            raise typer.Abort()

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_alias(alias)
        print_success(f"Alias '{alias}' dropped successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def alter(
    alias: str = typer.Argument(..., help="Alias name"),
    collection: str = typer.Argument(..., help="New collection name"),
) -> None:
    """Alter an alias to point to a different collection."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.alter_alias(collection, alias)
        print_success(f"Alias '{alias}' now points to collection '{collection}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
