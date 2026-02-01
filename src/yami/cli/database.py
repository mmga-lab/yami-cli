"""Database management commands."""

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


@app.command("alter-properties")
def alter_properties(
    name: str = typer.Argument(..., help="Database name"),
    props: Annotated[
        list[str] | None,
        typer.Option(
            "--prop",
            "-p",
            help="Property in key=value format (can be repeated)",
        ),
    ] = None,
) -> None:
    """Alter database properties.

    \b
    Examples:
      yami database alter-properties my_db -p database.replica.number=2
    """
    if not props:
        print_error("At least one --prop is required")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        properties = _parse_properties(props)
        client.alter_database_properties(db_name=name, properties=properties)
        print_success(f"Updated {len(properties)} property(ies) on database '{name}'")
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("drop-properties")
def drop_properties(
    name: str = typer.Argument(..., help="Database name"),
    keys: Annotated[
        list[str] | None,
        typer.Option(
            "--key",
            "-k",
            help="Property key to drop (can be repeated)",
        ),
    ] = None,
) -> None:
    """Drop database properties.

    \b
    Examples:
      yami database drop-properties my_db -k database.replica.number
    """
    if not keys:
        print_error("At least one --key is required")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_database_properties(db_name=name, property_keys=keys)
        print_success(f"Dropped {len(keys)} property(ies) from database '{name}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
