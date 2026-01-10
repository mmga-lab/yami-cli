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
    output: str = typer.Argument(..., help="Output directory for Parquet files"),
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
        10000,
        "--batch-size",
        "-b",
        help="Rows per Parquet file",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum rows to export",
    ),
) -> None:
    """Export collection data to Parquet files in a directory.

    \b
    Output structure:
      output_dir/
        part_0.parquet
        part_1.parquet
        ...

    \b
    Examples:
      # Export entire collection
      yami io export my_col ./export_data

      # Export with filter
      yami io export my_col ./export_data -f "category == 'A'"

      # Export specific fields
      yami io export my_col ./export_data --fields "id,name,embedding"

      # 50000 rows per file
      yami io export my_col ./export_data --batch-size 50000
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    ctx = get_context()
    client = ctx.get_client()

    try:
        # Check collection exists
        if not client.has_collection(collection):
            print_error(f"Collection '{collection}' not found")
            raise typer.Exit(1)

        # Create output directory
        output_dir = Path(output).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

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

        # Export in batches
        total_rows = 0
        file_count = 0
        current_batch = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Exporting...", total=None)

            def write_batch(rows, part_num):
                if not rows:
                    return
                columns = {}
                for key in rows[0].keys():
                    columns[key] = [row[key] for row in rows]
                table = pa.table(columns)
                file_path = output_dir / f"part_{part_num}.parquet"
                pq.write_table(table, file_path)

            while True:
                batch = iterator.next()
                if not batch:
                    break

                current_batch.extend(batch)
                total_rows += len(batch)

                # Write when batch is full
                while len(current_batch) >= batch_size:
                    write_batch(current_batch[:batch_size], file_count)
                    current_batch = current_batch[batch_size:]
                    file_count += 1

                progress.update(task, description=f"Exported {total_rows} rows, {file_count} files...")

            # Write remaining
            if current_batch:
                write_batch(current_batch, file_count)
                file_count += 1

        if total_rows == 0:
            print_info("No data to export")
            return

        print_success(f"Exported {total_rows} rows to {file_count} file(s) in {output_dir}")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("import")
def import_data(
    collection: str = typer.Argument(..., help="Collection name"),
    input_path: str = typer.Argument(..., help="Input Parquet file or directory"),
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
    """Import data from Parquet file(s) to collection.

    \b
    Supports:
      - Single Parquet file
      - Directory containing multiple Parquet files

    \b
    Examples:
      # Import from single file
      yami io import my_col data.parquet

      # Import from directory (all .parquet files)
      yami io import my_col ./export_data/

      # Import with SQL transformation
      yami io import my_col ./data/ --sql "SELECT id, name, vec FROM data WHERE score > 10"
    """
    try:
        import duckdb
    except ImportError:
        print_error("duckdb is required. Install with: uv add duckdb")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        # Check path exists
        path = Path(input_path)
        if not path.exists():
            print_error(f"Path not found: {input_path}")
            raise typer.Exit(1)

        # Check collection exists
        if not client.has_collection(collection):
            print_error(f"Collection '{collection}' not found")
            raise typer.Exit(1)

        # Determine parquet source
        if path.is_dir():
            # Read all parquet files in directory
            parquet_files = sorted(path.glob("*.parquet"))
            if not parquet_files:
                print_error(f"No .parquet files found in {input_path}")
                raise typer.Exit(1)
            # DuckDB can read glob pattern
            source = f"'{path}/*.parquet'"
            print_info(f"Found {len(parquet_files)} Parquet file(s)")
        else:
            source = f"'{path}'"

        # Read data with DuckDB
        conn = duckdb.connect()

        if sql:
            # Replace 'data' placeholder with actual source
            query = sql.replace("data", source)
        else:
            query = f"SELECT * FROM {source}"

        # Get total count
        count_result = conn.execute(f"SELECT COUNT(*) FROM ({query})").fetchone()
        total_rows = count_result[0] if count_result else 0

        if total_rows == 0:
            print_info("No data to import")
            conn.close()
            return

        print_info(f"Total rows to import: {total_rows}")

        # Process in batches using DuckDB's streaming
        total_inserted = 0
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Importing...", total=total_rows)

            # Use LIMIT/OFFSET for batching
            offset = 0
            while offset < total_rows:
                batch_query = f"SELECT * FROM ({query}) LIMIT {batch_size} OFFSET {offset}"
                result = conn.execute(batch_query)
                columns = [desc[0] for desc in result.description]

                batch_data = []
                for row in result.fetchall():
                    row_dict = {}
                    for i, col in enumerate(columns):
                        val = row[i]
                        if hasattr(val, 'tolist'):
                            val = val.tolist()
                        row_dict[col] = val
                    batch_data.append(row_dict)

                if batch_data:
                    client.insert(collection_name=collection, data=batch_data)
                    total_inserted += len(batch_data)
                    progress.update(task, advance=len(batch_data), description=f"Imported {total_inserted}/{total_rows} rows...")

                offset += batch_size

        conn.close()
        print_success(f"Imported {total_inserted} rows to '{collection}'")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
