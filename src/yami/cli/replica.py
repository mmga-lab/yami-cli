"""Replica management commands."""

from __future__ import annotations

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


@app.command()
def describe(
    collection: str = typer.Argument(..., help="Collection name"),
) -> None:
    """Describe replicas for a collection.

    Shows information about replica distribution across query nodes.
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        info = client.describe_replica(collection)
        format_output(info, ctx.output, title=f"Replicas: {collection}")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def transfer(
    source: str = typer.Argument(..., help="Source resource group name"),
    target: str = typer.Argument(..., help="Target resource group name"),
    collection: str = typer.Option(
        ...,
        "--collection",
        "-c",
        help="Collection name",
    ),
    num: int = typer.Option(
        1,
        "--num",
        "-n",
        help="Number of replicas to transfer",
    ),
) -> None:
    """Transfer replicas between resource groups.

    \b
    Examples:
      yami replica transfer rg1 rg2 -c my_collection -n 1
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        client.transfer_replica(
            source_group=source,
            target_group=target,
            collection_name=collection,
            num_replicas=num,
        )
        print_success(
            f"Transferred {num} replica(s) of '{collection}' from '{source}' to '{target}'"
        )
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
