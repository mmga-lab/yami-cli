"""Configuration management commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from yami.config.loader import get_config_value, load_config, save_config, set_config_value
from yami.config.profiles import (
    ConnectionProfile,
    add_profile,
    list_profile_names,
    load_profiles,
    remove_profile,
)
from yami.config.settings import get_config_dir
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)
profile_app = typer.Typer(no_args_is_help=True, help="Manage connection profiles")
app.add_typer(profile_app, name="profile")

console = Console()


@app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key (e.g., 'defaults.output')"),
) -> None:
    """Get a configuration value."""
    value = get_config_value(key)
    if value is None:
        print_error(f"Configuration key '{key}' not found")
        raise typer.Exit(1)
    console.print(f"{key} = {value}")


@app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key (e.g., 'defaults.output')"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a configuration value."""
    # Try to convert to appropriate type
    if value.lower() == "true":
        typed_value = True
    elif value.lower() == "false":
        typed_value = False
    else:
        try:
            typed_value = float(value)
            if typed_value.is_integer():
                typed_value = int(typed_value)
        except ValueError:
            typed_value = value

    set_config_value(key, typed_value)
    print_success(f"Set {key} = {typed_value}")


@app.command("list")
def config_list() -> None:
    """List all configuration values."""
    config = load_config()
    config_dict = {
        "default_profile": config.default_profile or "(not set)",
        "default_output": config.default_output,
        "timeout": config.timeout,
        "config_dir": str(get_config_dir()),
    }
    format_output(config_dict, "table", title="Configuration")


@app.command("init")
def config_init() -> None:
    """Initialize configuration directory and files."""
    from yami.config.settings import get_config_file, get_profiles_file

    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = get_config_file()
    if not config_file.exists():
        save_config(load_config())
        print_success(f"Created config file: {config_file}")
    else:
        console.print(f"Config file already exists: {config_file}")

    profiles_file = get_profiles_file()
    if not profiles_file.exists():
        # Create empty profiles file
        profiles_file.write_text("[profiles]\n")
        print_success(f"Created profiles file: {profiles_file}")
    else:
        console.print(f"Profiles file already exists: {profiles_file}")


# Profile subcommands


@profile_app.command("list")
def profile_list() -> None:
    """List all connection profiles."""
    profiles = load_profiles()
    config = load_config()
    default_profile = config.default_profile

    if not profiles:
        console.print("[yellow]No profiles configured. Use 'yami config profile add' to create one.[/yellow]")
        return

    profile_list = []
    for name, profile in profiles.items():
        profile_list.append({
            "name": name,
            "uri": profile.uri,
            "db": profile.db or "(default)",
            "default": "*" if name == default_profile else "",
        })

    format_output(profile_list, "table", title="Connection Profiles")


@profile_app.command("add")
def profile_add(
    name: str = typer.Argument(..., help="Profile name"),
    uri: str = typer.Option(
        ...,
        "--uri",
        "-u",
        help="Milvus server URI",
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        "-t",
        help="Authentication token",
    ),
    db: Optional[str] = typer.Option(
        None,
        "--db",
        "-d",
        help="Database name",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        help="Profile description",
    ),
    set_default: bool = typer.Option(
        False,
        "--default",
        help="Set as default profile",
    ),
) -> None:
    """Add a new connection profile."""
    profile = ConnectionProfile(
        name=name,
        uri=uri,
        token=token or "",
        db=db or "",
        description=description or "",
    )

    add_profile(profile)
    print_success(f"Profile '{name}' added successfully")

    if set_default:
        config = load_config()
        config.default_profile = name
        save_config(config)
        print_success(f"Profile '{name}' set as default")


@profile_app.command("remove")
def profile_remove(
    name: str = typer.Argument(..., help="Profile name"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Remove a connection profile."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to remove profile '{name}'?")
        if not confirm:
            raise typer.Abort()

    try:
        remove_profile(name)
        print_success(f"Profile '{name}' removed successfully")

        # Clear default if it was the removed profile
        config = load_config()
        if config.default_profile == name:
            config.default_profile = ""
            save_config(config)
            console.print("[yellow]Default profile was cleared[/yellow]")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@profile_app.command("use")
def profile_use(
    name: str = typer.Argument(..., help="Profile name"),
) -> None:
    """Set the default connection profile."""
    profiles = list_profile_names()
    if name not in profiles:
        print_error(f"Profile '{name}' not found")
        raise typer.Exit(1)

    config = load_config()
    config.default_profile = name
    save_config(config)
    print_success(f"Default profile set to '{name}'")


@profile_app.command("show")
def profile_show(
    name: str = typer.Argument(..., help="Profile name"),
) -> None:
    """Show details of a connection profile."""
    profiles = load_profiles()
    if name not in profiles:
        print_error(f"Profile '{name}' not found")
        raise typer.Exit(1)

    profile = profiles[name]
    profile_dict = {
        "name": profile.name,
        "uri": profile.uri,
        "token": "****" if profile.token else "(not set)",
        "db": profile.db or "(default)",
        "description": profile.description or "(none)",
    }
    format_output(profile_dict, "table", title=f"Profile: {name}")
