"""Role management commands."""

from __future__ import annotations

from typing import Optional

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_roles() -> None:
    """List all roles."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        roles = client.list_roles()
        format_output(roles, ctx.output, title="Roles")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def describe(
    name: str = typer.Argument(..., help="Role name"),
) -> None:
    """Describe a role and its privileges."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        info = client.describe_role(name)
        format_output(info, ctx.output, title=f"Role: {name}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(..., help="Role name"),
) -> None:
    """Create a new role."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.create_role(name)
        print_success(f"Role '{name}' created successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def drop(
    name: str = typer.Argument(..., help="Role name"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation and force drop even if role has users",
    ),
) -> None:
    """Drop a role."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to drop role '{name}'?")
        if not confirm:
            raise typer.Abort()

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_role(name, force_drop=force)
        print_success(f"Role '{name}' dropped successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def grant(
    role: str = typer.Argument(..., help="Role name"),
    privilege: str = typer.Argument(..., help="Privilege name"),
    collection: str = typer.Option(
        "*",
        "--collection",
        "-c",
        help="Collection name (default: all collections)",
    ),
    db: Optional[str] = typer.Option(
        None,
        "--db",
        "-d",
        help="Database name",
    ),
) -> None:
    """Grant a privilege to a role."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.grant_privilege_v2(
            role_name=role,
            privilege=privilege,
            collection_name=collection,
            db_name=db or "",
        )
        print_success(f"Privilege '{privilege}' granted to role '{role}' on '{collection}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def revoke(
    role: str = typer.Argument(..., help="Role name"),
    privilege: str = typer.Argument(..., help="Privilege name"),
    collection: str = typer.Option(
        "*",
        "--collection",
        "-c",
        help="Collection name (default: all collections)",
    ),
    db: Optional[str] = typer.Option(
        None,
        "--db",
        "-d",
        help="Database name",
    ),
) -> None:
    """Revoke a privilege from a role."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.revoke_privilege_v2(
            role_name=role,
            privilege=privilege,
            collection_name=collection,
            db_name=db or "",
        )
        print_success(f"Privilege '{privilege}' revoked from role '{role}' on '{collection}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
