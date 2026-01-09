"""Output formatting utilities."""

from __future__ import annotations

import json
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table

console = Console()


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
    console.print_json(json.dumps(data, indent=2, default=str, ensure_ascii=False))


def print_yaml(data: Any) -> None:
    """Print data as YAML."""
    output = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    console.print(output)


def print_table(data: dict | list, title: str = "") -> None:
    """Print data as Rich table."""
    if data is None:
        console.print("[yellow]No data[/yellow]")
        return

    if isinstance(data, list):
        _print_list_table(data, title)
    elif isinstance(data, dict):
        _print_dict_table(data, title)
    else:
        console.print(str(data))


def _print_list_table(data: list, title: str = "") -> None:
    """Print a list as a table."""
    if not data:
        console.print("[yellow]No data found[/yellow]")
        return

    first_item = data[0]

    if isinstance(first_item, str):
        # Simple string list
        table = Table(title=title, show_header=True)
        table.add_column("Name", style="cyan")
        for item in data:
            table.add_row(item)
        console.print(table)

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

        console.print(table)

    else:
        # Other types - just print
        for item in data:
            console.print(str(item))


def _print_dict_table(data: dict, title: str = "") -> None:
    """Print a dict as a key-value table."""
    table = Table(title=title, show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    for key, value in data.items():
        if isinstance(value, (list, dict)):
            value = json.dumps(value, indent=2, ensure_ascii=False)
        table.add_row(str(key), str(value) if value is not None else "")

    console.print(table)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]{message}[/blue]")
