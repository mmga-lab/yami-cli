"""Resource group management commands."""

from __future__ import annotations

import json

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_resource_groups() -> None:
    """List all resource groups."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        groups = client.list_resource_groups()
        format_output(groups, ctx.output, title="Resource Groups")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def describe(
    name: str = typer.Argument(..., help="Resource group name"),
) -> None:
    """Describe a resource group."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        info = client.describe_resource_group(name)
        format_output(info, ctx.output, title=f"Resource Group: {name}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(..., help="Resource group name"),
    config: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Resource group config as JSON (e.g., '{\"requests\": {\"node_num\": 1}}')",
    ),
) -> None:
    """Create a new resource group.

    \b
    Examples:
      yami resource-group create my_group
      yami resource-group create my_group -c '{"requests": {"node_num": 1}}'
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        kwargs = {}
        if config:
            kwargs["config"] = json.loads(config)

        client.create_resource_group(name, **kwargs)
        print_success(f"Resource group '{name}' created successfully")
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON config: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def drop(
    name: str = typer.Argument(..., help="Resource group name"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Drop a resource group."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to drop resource group '{name}'?")
        if not confirm:
            raise typer.Abort()

    ctx = get_context()
    client = ctx.get_client()

    try:
        client.drop_resource_group(name)
        print_success(f"Resource group '{name}' dropped successfully")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def update(
    configs: str = typer.Argument(
        ...,
        help="Resource group configs as JSON (e.g., '{\"group1\": {...}}')",
    ),
) -> None:
    """Update resource group configurations.

    \b
    The configs argument should be a JSON object mapping group names to their configs.

    \b
    Examples:
      yami resource-group update '{"my_group": {"requests": {"node_num": 2}}}'
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        configs_dict = json.loads(configs)
        client.update_resource_groups(configs_dict)
        print_success(f"Updated {len(configs_dict)} resource group(s)")
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
