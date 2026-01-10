"""Segment information commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_info

app = typer.Typer(no_args_is_help=True)
console = Console()


def _format_size(size_bytes: int) -> str:
    """Format byte size to human readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def _state_name(state: int) -> str:
    """Convert segment state enum to string."""
    states = {
        0: "SegmentStateNone",
        1: "NotExist",
        2: "Growing",
        3: "Sealed",
        4: "Flushed",
        5: "Flushing",
        6: "Dropped",
        7: "Importing",
    }
    return states.get(state, f"Unknown({state})")


def _level_name(level: int) -> str:
    """Convert segment level enum to string."""
    levels = {
        0: "Legacy",
        1: "L0",
        2: "L1",
        3: "L2",
    }
    return levels.get(level, f"Unknown({level})")


@app.command("loaded")
def segment_loaded(
    collection: str = typer.Argument(..., help="Collection name"),
) -> None:
    """List loaded segments for a collection.

    Shows segments currently loaded in memory for querying.
    Includes memory usage information.
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        segments = client.list_loaded_segments(collection)

        if not segments:
            print_info(f"No loaded segments found for '{collection}'")
            print_info("Make sure the collection is loaded.")
            return

        if ctx.output in ("json", "yaml"):
            # Convert to dict for JSON/YAML output
            result = {
                "collection": collection,
                "count": len(segments),
                "segments": [
                    {
                        "segment_id": s.segment_id,
                        "num_rows": s.num_rows,
                        "mem_size": s.mem_size,
                        "state": _state_name(s.state),
                        "level": _level_name(s.level),
                        "is_sorted": s.is_sorted,
                        "storage_version": s.storage_version,
                    }
                    for s in segments
                ],
            }
            format_output(result, ctx.output, title="Loaded Segments")
        else:
            # Table output
            table = Table(title=f"Loaded Segments - {collection}")
            table.add_column("Segment ID", style="cyan")
            table.add_column("Rows", justify="right", style="green")
            table.add_column("Memory", justify="right", style="yellow")
            table.add_column("State")
            table.add_column("Level")
            table.add_column("Sorted")

            total_rows = 0
            total_mem = 0
            for s in segments:
                total_rows += s.num_rows
                total_mem += s.mem_size
                table.add_row(
                    str(s.segment_id),
                    f"{s.num_rows:,}",
                    _format_size(s.mem_size),
                    _state_name(s.state),
                    _level_name(s.level),
                    "Yes" if s.is_sorted else "No",
                )

            console.print(table)
            console.print(
                f"\nTotal: {len(segments)} segments, {total_rows:,} rows, {_format_size(total_mem)}"
            )

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("persistent")
def segment_persistent(
    collection: str = typer.Argument(..., help="Collection name"),
) -> None:
    """List persistent segments for a collection.

    Shows all segments stored on disk, including sealed and flushed segments.
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        segments = client.list_persistent_segments(collection)

        if not segments:
            print_info(f"No persistent segments found for '{collection}'")
            return

        if ctx.output in ("json", "yaml"):
            # Convert to dict for JSON/YAML output
            result = {
                "collection": collection,
                "count": len(segments),
                "segments": [
                    {
                        "segment_id": s.segment_id,
                        "num_rows": s.num_rows,
                        "state": _state_name(s.state),
                        "level": _level_name(s.level),
                        "is_sorted": s.is_sorted,
                        "storage_version": s.storage_version,
                    }
                    for s in segments
                ],
            }
            format_output(result, ctx.output, title="Persistent Segments")
        else:
            # Table output
            table = Table(title=f"Persistent Segments - {collection}")
            table.add_column("Segment ID", style="cyan")
            table.add_column("Rows", justify="right", style="green")
            table.add_column("State")
            table.add_column("Level")
            table.add_column("Sorted")
            table.add_column("Storage Ver", justify="right")

            total_rows = 0
            for s in segments:
                total_rows += s.num_rows
                table.add_row(
                    str(s.segment_id),
                    f"{s.num_rows:,}",
                    _state_name(s.state),
                    _level_name(s.level),
                    "Yes" if s.is_sorted else "No",
                    str(s.storage_version),
                )

            console.print(table)
            console.print(f"\nTotal: {len(segments)} segments, {total_rows:,} rows")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("stats")
def segment_stats(
    collection: str = typer.Argument(..., help="Collection name"),
) -> None:
    """Show segment statistics for a collection.

    Provides a summary of segment counts by state and level.
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        segments = client.list_persistent_segments(collection)

        if not segments:
            print_info(f"No segments found for '{collection}'")
            return

        # Aggregate stats
        total_rows = 0
        by_state: dict[str, int] = {}
        by_level: dict[str, int] = {}
        rows_by_level: dict[str, int] = {}

        for s in segments:
            total_rows += s.num_rows
            state = _state_name(s.state)
            level = _level_name(s.level)

            by_state[state] = by_state.get(state, 0) + 1
            by_level[level] = by_level.get(level, 0) + 1
            rows_by_level[level] = rows_by_level.get(level, 0) + s.num_rows

        result = {
            "collection": collection,
            "total_segments": len(segments),
            "total_rows": total_rows,
            "by_state": by_state,
            "by_level": by_level,
            "rows_by_level": rows_by_level,
        }

        if ctx.output in ("json", "yaml"):
            format_output(result, ctx.output, title="Segment Statistics")
        else:
            console.print(f"\n[bold]Segment Statistics - {collection}[/bold]\n")
            console.print(f"Total Segments: [cyan]{len(segments)}[/cyan]")
            console.print(f"Total Rows: [green]{total_rows:,}[/green]\n")

            # State breakdown
            state_table = Table(title="By State")
            state_table.add_column("State")
            state_table.add_column("Count", justify="right")
            for state, count in sorted(by_state.items()):
                state_table.add_row(state, str(count))
            console.print(state_table)

            # Level breakdown
            console.print()
            level_table = Table(title="By Level")
            level_table.add_column("Level")
            level_table.add_column("Segments", justify="right")
            level_table.add_column("Rows", justify="right")
            for level in ["L0", "L1", "L2", "Legacy"]:
                if level in by_level:
                    level_table.add_row(
                        level,
                        str(by_level[level]),
                        f"{rows_by_level[level]:,}",
                    )
            console.print(level_table)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
