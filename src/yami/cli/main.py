"""Main CLI entry point."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from yami.cli import (
    alias,
    collection,
    compact,
    completion,
    config,
    data,
    database,
    flush,
    index,
    io,
    load,
    partition,
    query,
    role,
    segment,
    server,
    user,
)
from yami.core.context import CLIContext, reset_context, set_context
from yami.output.formatter import print_error, print_success
from yami.version import __version__

console = Console()

app = typer.Typer(
    name="yami",
    help="Yami - Yet Another Milvus Interface. A CLI tool for Milvus vector database.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register subcommands
app.add_typer(collection.app, name="collection", help="Collection operations")
app.add_typer(index.app, name="index", help="Index operations")
app.add_typer(partition.app, name="partition", help="Partition operations")
app.add_typer(database.app, name="database", help="Database operations")
app.add_typer(data.app, name="data", help="Data operations (insert/upsert/delete)")
app.add_typer(query.app, name="query", help="Query operations (search/query/get)")
app.add_typer(load.app, name="load", help="Load/Release operations")
app.add_typer(alias.app, name="alias", help="Alias operations")
app.add_typer(user.app, name="user", help="User management")
app.add_typer(role.app, name="role", help="Role management")
app.add_typer(server.app, name="server", help="Server information")
app.add_typer(config.app, name="config", help="Configuration management")
app.add_typer(completion.app, name="completion", help="Shell completion management")
app.add_typer(flush.app, name="flush", help="Flush operations")
app.add_typer(compact.app, name="compact", help="Compaction operations")
app.add_typer(segment.app, name="segment", help="Segment information")
app.add_typer(io.app, name="io", help="Import/Export data")


def version_callback(value: bool) -> None:
    """Handle --version flag."""
    if value:
        console.print(f"yami version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    uri: Optional[str] = typer.Option(
        None,
        "--uri",
        "-u",
        help="Milvus server URI (e.g., http://localhost:19530)",
        envvar="MILVUS_URI",
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        "-t",
        help="Authentication token",
        envvar="MILVUS_TOKEN",
    ),
    db: Optional[str] = typer.Option(
        None,
        "--db",
        "-d",
        help="Database name",
    ),
    profile: Optional[str] = typer.Option(
        None,
        "--profile",
        "-p",
        help="Connection profile name",
    ),
    output: str = typer.Option(
        "table",
        "--output",
        "-o",
        help="Output format: table, json, yaml",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Yami - Yet Another Milvus Interface.

    A powerful CLI tool for managing Milvus vector database.
    """
    # If no command is invoked, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()

    # Create and store context
    cli_ctx = CLIContext(
        uri=uri,
        token=token,
        db=db,
        profile=profile,
        output=output,
    )
    set_context(cli_ctx)

    # Store in typer context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["cli_ctx"] = cli_ctx


@app.command()
def connect(
    uri: str = typer.Argument(
        ...,
        help="Milvus server URI (e.g., http://localhost:19530)",
    ),
    token: str = typer.Option(
        "",
        "--token",
        "-t",
        help="Authentication token",
    ),
    db: str = typer.Option(
        "",
        "--db",
        "-d",
        help="Database name",
    ),
) -> None:
    """Test connection to Milvus server."""
    from yami.core.client import YamiClient

    try:
        client = YamiClient(uri=uri, token=token, db_name=db)
        version = client.get_server_version()
        client.close()
        print_success(f"Connected to Milvus at {uri}")
        console.print(f"Server version: {version}")
    except Exception as e:
        print_error(f"Failed to connect: {e}")
        raise typer.Exit(1)


def main() -> None:
    """Main entry point."""
    try:
        app()
    finally:
        reset_context()


if __name__ == "__main__":
    main()
