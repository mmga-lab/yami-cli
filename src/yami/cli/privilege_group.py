"""Privilege group management commands."""

from __future__ import annotations

from typing import Annotated

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_privilege_groups() -> None:
    """List all privilege groups."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        groups = client.list_privilege_groups()
        format_output(groups, ctx.output, title="Privilege Groups")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(..., help="Privilege group name"),
) -> None:
    """Create a new privilege group."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.create_privilege_group(name)
        print_success(f"Privilege group '{name}' created successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def drop(
    name: str = typer.Argument(..., help="Privilege group name"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Drop a privilege group."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to drop privilege group '{name}'?")
        if not confirm:
            raise typer.Abort()

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_privilege_group(name)
        print_success(f"Privilege group '{name}' dropped successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def add(
    name: str = typer.Argument(..., help="Privilege group name"),
    privileges: Annotated[
        list[str] | None,
        typer.Option(
            "--privilege",
            "-p",
            help="Privilege to add (can be repeated)",
        ),
    ] = None,
) -> None:
    """Add privileges to a privilege group.

    \b
    Examples:
      yami privilege-group add my_group -p Insert -p Query
      yami privilege-group add my_group --privilege Search
    """
    if not privileges:
        print_error("At least one --privilege is required")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.add_privileges_to_group(group_name=name, privileges=privileges)
        print_success(f"Added {len(privileges)} privilege(s) to group '{name}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def remove(
    name: str = typer.Argument(..., help="Privilege group name"),
    privileges: Annotated[
        list[str] | None,
        typer.Option(
            "--privilege",
            "-p",
            help="Privilege to remove (can be repeated)",
        ),
    ] = None,
) -> None:
    """Remove privileges from a privilege group.

    \b
    Examples:
      yami privilege-group remove my_group -p Insert -p Query
      yami privilege-group remove my_group --privilege Search
    """
    if not privileges:
        print_error("At least one --privilege is required")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.remove_privileges_from_group(group_name=name, privileges=privileges)
        print_success(f"Removed {len(privileges)} privilege(s) from group '{name}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
