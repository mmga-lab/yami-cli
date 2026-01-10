"""Output formatting utilities."""

from __future__ import annotations

import json
import sys
from typing import Any

import yaml
from rich.console import Console

# Default consoles (for human mode)
_console: Console | None = None
_stderr_console: Console | None = None


def _is_agent_mode() -> bool:
    """Check if running in agent mode."""
    try:
        from yami.core.context import get_context
        return get_context().is_agent_mode
    except Exception:
        return False


def _get_console() -> Console:
    """Get stdout console, with colors disabled in agent mode."""
    global _console
    if _is_agent_mode():
        # Agent mode: no colors, no markup
        return Console(force_terminal=False, no_color=True)
    if _console is None:
        _console = Console()
    return _console


def _get_stderr_console() -> Console:
    """Get stderr console, with colors disabled in agent mode."""
    global _stderr_console
    if _is_agent_mode():
        return Console(file=sys.stderr, force_terminal=False, no_color=True)
    if _stderr_console is None:
        _stderr_console = Console(file=sys.stderr)
    return _stderr_console


def _get_output_format() -> str:
    """Get current output format from context."""
    try:
        from yami.core.context import get_context
        return get_context().output
    except Exception:
        return "table"


def _is_quiet() -> bool:
    """Check if quiet mode is enabled."""
    try:
        from yami.core.context import get_context
        return get_context().quiet
    except Exception:
        return False


def format_output(
    data: dict | list | Any,
    output_format: str = "table",
    title: str = "",
) -> None:
    """Format and output data based on specified format.

    Args:
        data: The data to output.
        output_format: Output format - 'table', 'json', or 'yaml'.
        title: Optional title for table output.
    """
    if output_format == "json":
        print_json(data)
    elif output_format == "yaml":
        print_yaml(data)
    else:
        print_table(data, title)


def print_json(data: Any) -> None:
    """Print data as JSON."""
    _get_console().print_json(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def print_yaml(data: Any) -> None:
    """Print data as YAML."""
    output = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    _get_console().print(output)


def print_table(data: dict | list, title: str = "") -> None:
    """Print data as Rich table."""
    from rich.table import Table

    if data is None:
        _get_console().print("[yellow]No data[/yellow]")
        return

    if isinstance(data, list):
        _print_list_table(data, title)
    elif isinstance(data, dict):
        _print_dict_table(data, title)
    else:
        _get_console().print(str(data))


def _print_list_table(data: list, title: str = "") -> None:
    """Print a list as a table."""
    from rich.table import Table

    if not data:
        _get_console().print("[yellow]No data found[/yellow]")
        return

    first_item = data[0]

    if isinstance(first_item, str):
        # Simple string list
        table = Table(title=title, show_header=True)
        table.add_column("Name", style="cyan")
        for item in data:
            table.add_row(item)
        _get_console().print(table)

    elif isinstance(first_item, dict):
        # List of dicts
        table = Table(title=title, show_header=True)
        keys = list(first_item.keys())

        for i, key in enumerate(keys):
            style = "cyan" if i == 0 else None
            table.add_column(str(key), style=style)

        for item in data:
            row_values = []
            for k in keys:
                val = item.get(k, "")
                if isinstance(val, (list, dict)):
                    val = json.dumps(val, ensure_ascii=False)
                row_values.append(str(val) if val is not None else "")
            table.add_row(*row_values)

        _get_console().print(table)

    else:
        # Other types - just print
        for item in data:
            _get_console().print(str(item))


def _print_dict_table(data: dict, title: str = "") -> None:
    """Print a dict as a key-value table."""
    from rich.table import Table

    table = Table(title=title, show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    for key, value in data.items():
        if isinstance(value, (list, dict)):
            value = json.dumps(value, indent=2, ensure_ascii=False)
        table.add_row(str(key), str(value) if value is not None else "")

    _get_console().print(table)


def print_success(message: str, data: dict | None = None) -> None:
    """Print a success message.

    In JSON mode, outputs structured response.
    In quiet mode, suppresses output unless data is provided.
    """
    output_format = _get_output_format()
    quiet = _is_quiet()

    if output_format == "json":
        result = {"status": "success", "message": message}
        if data:
            result["data"] = data
        _get_console().print_json(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    elif not quiet:
        _get_console().print(f"[green]{message}[/green]")


def print_error(message: str, code: str = "ERROR") -> None:
    """Print an error message.

    In JSON mode, outputs structured error to stdout.
    Otherwise outputs to stderr for clean stdout.
    """
    output_format = _get_output_format()

    if output_format == "json":
        error_data = {"error": {"code": code, "message": message}}
        _get_console().print_json(json.dumps(error_data, indent=2, ensure_ascii=False))
    else:
        _get_stderr_console().print(f"[red]Error:[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message to stderr."""
    if not _is_quiet():
        _get_stderr_console().print(f"[yellow]Warning:[/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message to stderr.

    Outputs to stderr to keep stdout clean for data.
    Suppressed in quiet mode.
    """
    if not _is_quiet():
        _get_stderr_console().print(f"[blue]{message}[/blue]")
