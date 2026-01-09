"""User management commands."""

from __future__ import annotations

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_users() -> None:
    """List all users."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        users = client.list_users()
        format_output(users, ctx.output, title="Users")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def describe(
    name: str = typer.Argument(..., help="Username"),
) -> None:
    """Describe a user."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        info = client.describe_user(name)
        format_output(info, ctx.output, title=f"User: {name}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(..., help="Username"),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Password",
    ),
) -> None:
    """Create a new user."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.create_user(name, password)
        print_success(f"User '{name}' created successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def drop(
    name: str = typer.Argument(..., help="Username"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Drop a user."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to drop user '{name}'?")
        if not confirm:
            raise typer.Abort()

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_user(name)
        print_success(f"User '{name}' dropped successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("update-password")
def update_password(
    name: str = typer.Argument(..., help="Username"),
    old_password: str = typer.Option(
        ...,
        "--old-password",
        prompt="Old password",
        hide_input=True,
        help="Current password",
    ),
    new_password: str = typer.Option(
        ...,
        "--new-password",
        prompt="New password",
        hide_input=True,
        confirmation_prompt=True,
        help="New password",
    ),
) -> None:
    """Update a user's password."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.update_password(name, old_password, new_password)
        print_success(f"Password updated for user '{name}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("grant-role")
def grant_role(
    user: str = typer.Argument(..., help="Username"),
    role: str = typer.Argument(..., help="Role name"),
) -> None:
    """Grant a role to a user."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.grant_role(user, role)
        print_success(f"Role '{role}' granted to user '{user}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("revoke-role")
def revoke_role(
    user: str = typer.Argument(..., help="Username"),
    role: str = typer.Argument(..., help="Role name"),
) -> None:
    """Revoke a role from a user."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.revoke_role(user, role)
        print_success(f"Role '{role}' revoked from user '{user}'")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
