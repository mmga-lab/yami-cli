"""Diagnostics and troubleshooting commands."""

from __future__ import annotations

import platform
import sys

import typer
from rich.console import Console
from rich.table import Table

from yami.config.loader import load_config
from yami.config.profiles import get_profile, load_profiles
from yami.config.settings import get_config_dir, get_config_file, get_profiles_file
from yami.output.formatter import print_debug
from yami.version import __version__

app = typer.Typer(invoke_without_command=True)
console = Console()


def _check_mark(ok: bool) -> str:
    """Return a check mark or cross based on status."""
    return "[green]✓[/green]" if ok else "[red]✗[/red]"


def _warn_mark() -> str:
    """Return a warning mark."""
    return "[yellow]![/yellow]"


@app.callback(invoke_without_command=True)
def doctor(
    ctx: typer.Context,
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="Profile to test (default: current profile)",
    ),
) -> None:
    """Run diagnostics to check environment and configuration.

    Checks:
    - Yami, Python, and pymilvus versions
    - Configuration files
    - Profile settings
    - Server connectivity
    """
    if ctx.invoked_subcommand is not None:
        return

    console.print()
    console.print("[bold]Yami Diagnostics[/bold]")
    console.print("=" * 40)

    warnings: list[str] = []

    # Version info
    console.print("\n[bold cyan]Versions[/bold cyan]")
    _check_versions(warnings)

    # Configuration
    console.print("\n[bold cyan]Configuration[/bold cyan]")
    _check_configuration(warnings)

    # Profile and connection
    console.print("\n[bold cyan]Connection Test[/bold cyan]")
    _check_connection(profile, warnings)

    # Warnings summary
    if warnings:
        console.print("\n[yellow][!] Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  • {warning}")

    # Final status
    console.print()
    if not warnings:
        console.print("[bold green]All checks passed![/bold green]")
    else:
        console.print(f"[yellow]Completed with {len(warnings)} warning(s)[/yellow]")
    console.print()


def _check_versions(warnings: list[str]) -> None:
    """Check version information."""
    # Yami version
    console.print(f"  {_check_mark(True)} Yami version: {__version__}")

    # Python version
    py_version = platform.python_version()
    py_ok = sys.version_info >= (3, 10)
    console.print(f"  {_check_mark(py_ok)} Python version: {py_version}")
    if not py_ok:
        warnings.append(f"Python 3.10+ required (current: {py_version})")

    # pymilvus version
    try:
        import pymilvus

        pymilvus_version = pymilvus.__version__
        console.print(f"  {_check_mark(True)} pymilvus version: {pymilvus_version}")

        # Check for newer version (optional)
        _check_pymilvus_update(pymilvus_version, warnings)
    except ImportError:
        console.print(f"  {_check_mark(False)} pymilvus: not installed")
        warnings.append("pymilvus is not installed")


def _check_pymilvus_update(current_version: str, warnings: list[str]) -> None:
    """Check if a newer pymilvus version is available."""
    try:
        # Just check major.minor for compatibility
        parts = current_version.split(".")
        if len(parts) >= 2:
            major_minor = f"{parts[0]}.{parts[1]}"
            # We just note the version, not actively check PyPI
            print_debug(f"pymilvus {major_minor}.x installed")
    except Exception:
        pass


def _check_configuration(warnings: list[str]) -> None:
    """Check configuration files."""
    # Config directory
    config_dir = get_config_dir()
    dir_exists = config_dir.exists()
    console.print(f"  {_check_mark(dir_exists)} Config directory: {config_dir}")
    if not dir_exists:
        warnings.append(f"Config directory does not exist: {config_dir}")

    # Config file
    config_file = get_config_file()
    file_exists = config_file.exists()
    if file_exists:
        console.print(f"  {_check_mark(True)} Config file: {config_file}")
    else:
        console.print(f"  {_warn_mark()} Config file: not found (using defaults)")

    # Profiles file
    profiles_file = get_profiles_file()
    profiles_exists = profiles_file.exists()
    if profiles_exists:
        console.print(f"  {_check_mark(True)} Profiles file: {profiles_file}")
    else:
        console.print(f"  {_warn_mark()} Profiles file: not found")

    # Active profile
    try:
        config = load_config()
        default_profile = config.default_profile
        if default_profile:
            console.print(f"  {_check_mark(True)} Active profile: {default_profile}")
        else:
            console.print(f"  {_warn_mark()} Active profile: (not set)")
    except Exception as e:
        console.print(f"  {_check_mark(False)} Config error: {e}")
        warnings.append(f"Failed to load config: {e}")


def _check_connection(profile_name: str | None, warnings: list[str]) -> None:
    """Check server connectivity."""
    from yami.core.client import YamiClient
    from yami.core.context import get_context

    # Determine which profile to test
    if not profile_name:
        try:
            config = load_config()
            profile_name = config.default_profile
        except Exception:
            pass

    # Get connection parameters
    uri = None
    token = ""
    db = ""

    if profile_name:
        try:
            profile = get_profile(profile_name)
            uri = profile.uri
            token = profile.token
            db = profile.db
            console.print(f"  Testing profile: [cyan]{profile_name}[/cyan]")
        except Exception:
            console.print(f"  {_check_mark(False)} Profile '{profile_name}' not found")
            warnings.append(f"Profile '{profile_name}' not found")
            return

    # Try context URI if no profile
    if not uri:
        try:
            ctx = get_context()
            if ctx.uri:
                uri = ctx.uri
        except Exception:
            pass

    if not uri:
        console.print(f"  {_warn_mark()} No URI configured")
        console.print("    Run: yami config profile add <name> --uri <uri>")
        warnings.append("No Milvus URI configured")
        return

    console.print(f"  URI: {uri}")

    # Test connection
    try:
        client = YamiClient(uri=uri, token=token, db_name=db, timeout=10.0)
        console.print(f"  {_check_mark(True)} Server reachable")

        # Get server version
        try:
            version = client.get_server_version()
            console.print(f"  {_check_mark(True)} Server version: {version}")
        except Exception:
            console.print(f"  {_warn_mark()} Could not get server version")

        # Check authentication status
        try:
            # Try a simple operation to verify auth
            client.list_collections()
            console.print(f"  {_check_mark(True)} Authentication: OK")
        except Exception as e:
            if "auth" in str(e).lower() or "permission" in str(e).lower():
                console.print(f"  {_check_mark(False)} Authentication: Failed")
                warnings.append("Authentication failed - check your token")
            else:
                console.print(f"  {_check_mark(True)} Authentication: OK")

        client.close()
    except Exception as e:
        console.print(f"  {_check_mark(False)} Connection failed: {e}")
        warnings.append(f"Cannot connect to {uri}")

        # Provide hints
        error_str = str(e).lower()
        if "connection refused" in error_str:
            console.print("    [dim]Hint: Is Milvus server running?[/dim]")
        elif "timeout" in error_str:
            console.print("    [dim]Hint: Check network connectivity[/dim]")
        elif "auth" in error_str:
            console.print("    [dim]Hint: Check authentication token[/dim]")


@app.command("profiles")
def doctor_profiles() -> None:
    """Show all configured profiles with their status."""
    console.print("\n[bold]Profile Status[/bold]")
    console.print("=" * 40)

    profiles = load_profiles()
    if not profiles:
        console.print("[yellow]No profiles configured.[/yellow]")
        console.print("Run: yami config profile add <name> --uri <uri>")
        return

    config = load_config()
    default_profile = config.default_profile

    table = Table(show_header=True)
    table.add_column("Profile", style="cyan")
    table.add_column("URI")
    table.add_column("Status")
    table.add_column("Default")

    from yami.core.client import YamiClient

    for name, profile in profiles.items():
        # Test connection
        try:
            client = YamiClient(
                uri=profile.uri,
                token=profile.token,
                db_name=profile.db,
                timeout=5.0,
            )
            client.close()
            status = "[green]OK[/green]"
        except Exception:
            status = "[red]Error[/red]"

        is_default = "✓" if name == default_profile else ""
        table.add_row(name, profile.uri, status, is_default)

    console.print(table)
    console.print()
