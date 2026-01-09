"""Server information commands."""

from __future__ import annotations

import typer
from rich.console import Console

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def version() -> None:
    """Get server version."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        ver = client.get_server_version()
        if ctx.output == "table":
            console.print(f"Server version: [cyan]{ver}[/cyan]")
        else:
            format_output({"version": ver}, ctx.output)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("type")
def server_type() -> None:
    """Get server type (milvus/zilliz)."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        stype = client.get_server_type()
        if ctx.output == "table":
            console.print(f"Server type: [cyan]{stype}[/cyan]")
        else:
            format_output({"type": stype}, ctx.output)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def info() -> None:
    """Get server information (version and type)."""
    ctx = get_context()
    client = ctx.get_client()

    try:
        info_data = {
            "uri": client.uri,
            "version": client.get_server_version(),
            "type": client.get_server_type(),
        }
        format_output(info_data, ctx.output, title="Server Info")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
