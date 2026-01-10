"""Compaction management commands."""

from __future__ import annotations

import typer
from rich.console import Console

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error, print_info, print_success

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("run")
def compact_run(
    collection: str = typer.Argument(..., help="Collection name"),
    clustering: bool = typer.Option(
        False,
        "--clustering",
        "-c",
        help="Trigger clustering compaction",
    ),
    l0: bool = typer.Option(
        False,
        "--l0",
        help="Trigger L0 compaction",
    ),
) -> None:
    """Start a compaction job to merge small segments.

    Returns a job ID that can be used to check the compaction status.

    \b
    Compaction types:
    - Default: Merge small segments into larger ones
    - Clustering (--clustering): Reorganize data by clustering key
    - L0 (--l0): Compact L0 segments only
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        job_id = client.compact(
            collection_name=collection,
            is_clustering=clustering,
            is_l0=l0,
        )

        result = {
            "job_id": job_id,
            "collection": collection,
            "type": "clustering" if clustering else ("l0" if l0 else "default"),
        }
        format_output(result, ctx.output, title="Compaction Started")

        print_info(f"Check status with: yami compact state {job_id}")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("state")
def compact_state(
    job_id: int = typer.Argument(..., help="Compaction job ID"),
) -> None:
    """Get the state of a compaction job.

    \b
    Possible states:
    - Executing: Compaction is in progress
    - Completed: Compaction finished successfully
    - UndefiedState: Unknown state
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        state = client.get_compaction_state(job_id)
        result = {
            "job_id": job_id,
            "state": state,
        }
        format_output(result, ctx.output, title="Compaction State")

        if state == "Completed":
            print_success("Compaction completed")
        elif state == "Executing":
            print_info("Compaction is still running...")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("plans")
def compact_plans(
    job_id: int = typer.Argument(..., help="Compaction job ID"),
) -> None:
    """Get detailed compaction plans for a job.

    Shows the segments being merged and the target segments.
    """
    ctx = get_context()
    client = ctx.get_client()

    try:
        plans = client.get_compaction_plans(job_id)

        # Convert plans to dict for output
        result = {
            "job_id": job_id,
            "state": plans.state_name if hasattr(plans, "state_name") else str(plans.state),
            "plans": [],
        }

        if hasattr(plans, "plans"):
            for plan in plans.plans:
                plan_info = {}
                if hasattr(plan, "sources"):
                    plan_info["sources"] = list(plan.sources)
                if hasattr(plan, "target"):
                    plan_info["target"] = plan.target
                result["plans"].append(plan_info)

        format_output(result, ctx.output, title="Compaction Plans")

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("wait")
def compact_wait(
    job_id: int = typer.Argument(..., help="Compaction job ID"),
    interval: float = typer.Option(
        2.0,
        "--interval",
        "-i",
        help="Polling interval in seconds",
    ),
    timeout: float = typer.Option(
        300.0,
        "--timeout",
        "-t",
        help="Maximum wait time in seconds",
    ),
) -> None:
    """Wait for a compaction job to complete.

    Polls the compaction state until it completes or times out.
    """
    import time

    ctx = get_context()
    client = ctx.get_client()

    start_time = time.time()

    try:
        with console.status(f"[bold blue]Waiting for compaction job {job_id}...") as status:
            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    print_error(f"Timeout after {timeout}s waiting for compaction")
                    raise typer.Exit(1)

                state = client.get_compaction_state(job_id)

                if state == "Completed":
                    print_success(f"Compaction job {job_id} completed in {elapsed:.1f}s")
                    return

                status.update(
                    f"[bold blue]Compaction state: {state} ({elapsed:.0f}s elapsed)..."
                )
                time.sleep(interval)

    except KeyboardInterrupt:
        print_info("Interrupted. Compaction continues in background.")
        raise typer.Exit(0)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
