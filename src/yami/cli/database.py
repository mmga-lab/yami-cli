"""Database management commands."""

from __future__ import annotations

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_databases() -> None:
    """List all databases."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        databases = client.list_databases()
        format_output(databases, ctx.output, title="Databases")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def describe(
    name: str = typer.Argument(..., help="Database name"),
) -> None:
    """Describe a database."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        info = client.describe_database(name)
        format_output(info, ctx.output, title=f"Database: {name}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(..., help="Database name"),
) -> None:
    """Create a database."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.create_database(name)
        print_success(f"Database '{name}' created successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def drop(
    name: str = typer.Argument(..., help="Database name"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Drop a database."""
    if name == "default":
        print_error("Cannot drop the default database")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Are you sure you want to drop database '{name}'?")
        if not confirm:
            raise typer.Abort()

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_database(name)
        print_success(f"Database '{name}' dropped successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def use(
    name: str = typer.Argument(..., help="Database name"),
) -> None:
    """Switch to a database."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.use_database(name)
        print_success(f"Switched to database '{name}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
