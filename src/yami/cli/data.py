"""Data manipulation commands (insert/upsert/delete)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_success

app = typer.Typer(no_args_is_help=True)


def _load_data_from_file(file_path: str) -> list[dict]:
    """Load data from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path) as f:
        data = json.load(f)

    if isinstance(data, dict):
        return [data]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("File must contain a JSON object or array of objects")


@app.command()
def insert(
    collection: str = typer.Argument(..., help="Collection name"),
    file: Optional[str] = typer.Option(
        None,
        "--file",
        "-f",
        help="JSON file containing data to insert",
    ),
    data_json: Optional[str] = typer.Option(
        None,
        "--data",
        "-d",
        help="JSON data to insert (inline)",
    ),
    partition: Optional[str] = typer.Option(
        None,
        "--partition",
        "-p",
        help="Partition name",
    ),
) -> None:
    """Insert data into a collection.

    Data can be provided via file (--file) or inline JSON (--data).
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        if file:
            data = _load_data_from_file(file)
        elif data_json:
            parsed = json.loads(data_json)
            data = [parsed] if isinstance(parsed, dict) else parsed
        else:
            print_error("Either --file or --data is required")
            raise typer.Exit(1)

        result = client.insert(
            collection_name=collection,
            data=data,
            partition_name=partition or "",
        )
        format_output(result, ctx.output, title="Insert Result")
    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def upsert(
    collection: str = typer.Argument(..., help="Collection name"),
    file: Optional[str] = typer.Option(
        None,
        "--file",
        "-f",
        help="JSON file containing data to upsert",
    ),
    data_json: Optional[str] = typer.Option(
        None,
        "--data",
        "-d",
        help="JSON data to upsert (inline)",
    ),
    partition: Optional[str] = typer.Option(
        None,
        "--partition",
        "-p",
        help="Partition name",
    ),
) -> None:
    """Upsert data into a collection.

    If an entity with the same primary key exists, it will be updated.
    Otherwise, a new entity will be inserted.
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        if file:
            data = _load_data_from_file(file)
        elif data_json:
            parsed = json.loads(data_json)
            data = [parsed] if isinstance(parsed, dict) else parsed
        else:
            print_error("Either --file or --data is required")
            raise typer.Exit(1)

        result = client.upsert(
            collection_name=collection,
            data=data,
            partition_name=partition or "",
        )
        format_output(result, ctx.output, title="Upsert Result")
    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command()
def delete(
    collection: str = typer.Argument(..., help="Collection name"),
    ids: Optional[str] = typer.Option(
        None,
        "--ids",
        "-i",
        help="Comma-separated list of IDs to delete",
    ),
    filter_expr: Optional[str] = typer.Option(
        None,
        "--filter",
        "-f",
        help="Filter expression (e.g., 'age > 20')",
    ),
    partition: Optional[str] = typer.Option(
        None,
        "--partition",
        "-p",
        help="Partition name",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Delete data from a collection.

    Delete by IDs (--ids) or by filter expression (--filter).
    """
    if not ids and not filter_expr:
        print_error("Either --ids or --filter is required")
        raise typer.Exit(1)

    if not force:
        if ids:
            confirm = typer.confirm(f"Delete entities with IDs: {ids}?")
        else:
            confirm = typer.confirm(f"Delete entities matching filter: {filter_expr}?")
        if not confirm:
            raise typer.Abort()

    ctx = get_context()
    client = ctx.get_client()

    try:
        kwargs = {"collection_name": collection}

        if ids:
            # Parse IDs - try as integers first, then strings
            id_list = [x.strip() for x in ids.split(",")]
            try:
                kwargs["ids"] = [int(x) for x in id_list]
            except ValueError:
                kwargs["ids"] = id_list

        if filter_expr:
            kwargs["filter"] = filter_expr

        if partition:
            kwargs["partition_name"] = partition

        result = client.delete(**kwargs)
        format_output(result, ctx.output, title="Delete Result")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
