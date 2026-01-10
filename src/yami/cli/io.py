"""Data import/export commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from yami.core.context import get_context
from yami.output.formatter import print_error, print_info, print_success

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("export")
def export_data(
    collection: str = typer.Argument(..., help="Collection name"),
    output: str = typer.Argument(..., help="Output Parquet file path"),
    filter_expr: Optional[str] = typer.Option(
        None,
        "--filter",
        "-f",
        help="Filter expression to export subset",
    ),
    fields: Optional[str] = typer.Option(
        None,
        "--fields",
        help="Comma-separated fields to export (default: all)",
    ),
    partition: Optional[str] = typer.Option(
        None,
        "--partition",
        "-p",
        help="Partition name to export from",
    ),
    batch_size: int = typer.Option(
        1000,
        "--batch-size",
        "-b",
        help="Batch size for reading",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum rows to export",
    ),
) -> None:
    """Export collection data to Parquet file.

    \b
    Examples:
      # Export entire collection
      yami io export my_col data.parquet

      # Export with filter
      yami io export my_col data.parquet -f "category == 'A'"

      # Export specific fields
      yami io export my_col data.parquet --fields "id,name,embedding"

      # Export first 1000 rows
      yami io export my_col data.parquet --limit 1000
    """
    try:
        import duckdb
    except ImportError:
        print_error("duckdb is required. Install with: uv add duckdb")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        # Check collection exists
        if not client.has_collection(collection):
            print_error(f"Collection '{collection}' not found")
            raise typer.Exit(1)

        # Parse fields
        output_fields = ["*"]
        if fields:
            output_fields = [f.strip() for f in fields.split(",")]

        # Parse partitions
        partitions = None
        if partition:
            partitions = [partition]

        # Get iterator
        iterator = client.query_iterator(
            collection_name=collection,
            batch_size=batch_size,
            limit=limit or -1,
            filter=filter_expr or "",
            output_fields=output_fields,
            partition_names=partitions,
        )

        # Collect all data
        all_rows = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Exporting...", total=None)

            while True:
                batch = iterator.next()
                if not batch:
                    break
                all_rows.extend(batch)
                progress.update(task, advance=len(batch), description=f"Exported {len(all_rows)} rows...")

        if not all_rows:
            print_info("No data to export")
            return

        # Write to Parquet using pyarrow
        import pyarrow as pa
        import pyarrow.parquet as pq

        # Convert to columnar format
        columns = {}
        for key in all_rows[0].keys():
            columns[key] = [row[key] for row in all_rows]

        table = pa.table(columns)
        output_path = Path(output).resolve()
        pq.write_table(table, output_path)

        print_success(f"Exported {len(all_rows)} rows to {output_path}")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("import")
def import_data(
    collection: str = typer.Argument(..., help="Collection name"),
    input_file: str = typer.Argument(..., help="Input Parquet file path"),
    batch_size: int = typer.Option(
        1000,
        "--batch-size",
        "-b",
        help="Batch size for inserting",
    ),
    sql: Optional[str] = typer.Option(
        None,
        "--sql",
        help="SQL to transform data before import",
    ),
) -> None:
    """Import data from Parquet file to collection.

    \b
    Examples:
      # Import from Parquet
      yami io import my_col data.parquet

      # Import with SQL transformation
      yami io import my_col data.parquet --sql "SELECT id, name, embedding FROM data"

      # Import with smaller batch size
      yami io import my_col data.parquet --batch-size 500
    """
    try:
        import duckdb
    except ImportError:
        print_error("duckdb is required. Install with: uv add duckdb")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        # Check file exists
        input_path = Path(input_file)
        if not input_path.exists():
            print_error(f"File not found: {input_file}")
            raise typer.Exit(1)

        # Check collection exists
        if not client.has_collection(collection):
            print_error(f"Collection '{collection}' not found")
            raise typer.Exit(1)

        # Read data with DuckDB
        conn = duckdb.connect()

        if sql:
            # Use custom SQL
            query = sql.replace("data", f"'{input_path}'")
        else:
            query = f"SELECT * FROM '{input_path}'"

        # Get total count
        count_result = conn.execute(f"SELECT COUNT(*) FROM ({query})").fetchone()
        total_rows = count_result[0] if count_result else 0

        if total_rows == 0:
            print_info("No data to import")
            conn.close()
            return

        # Read all data
        result = conn.execute(query)
        columns = [desc[0] for desc in result.description]

        # Convert to list of dicts
        all_data = []
        for row in result.fetchall():
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                # Convert numpy/duckdb types to Python types
                if hasattr(val, 'tolist'):
                    val = val.tolist()
                row_dict[col] = val
            all_data.append(row_dict)

        conn.close()

        # Insert in batches
        total_inserted = 0
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Importing...", total=total_rows)

            for i in range(0, len(all_data), batch_size):
                batch = all_data[i:i + batch_size]
                client.insert(collection_name=collection, data=batch)
                total_inserted += len(batch)
                progress.update(task, advance=len(batch), description=f"Imported {total_inserted}/{total_rows} rows...")

        print_success(f"Imported {total_inserted} rows to '{collection}'")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
