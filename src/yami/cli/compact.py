"""Compaction management commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from yami.core import job_cache
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

        compact_type = "clustering" if clustering else ("l0" if l0 else "default")
        result = {
            "job_id": job_id,
            "collection": collection,
            "type": compact_type,
        }
        format_output(result, ctx.output, title="Compaction Started")

        # Cache the job for later tracking
        job_cache.add_job(
            job_id=job_id,
            collection=collection,
            compact_type=compact_type,
            uri=ctx.get_uri(),
        )

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

        # Update cached job state
        job_cache.update_job_state(job_id, ctx.get_uri(), state)

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
                    job_cache.update_job_state(job_id, ctx.get_uri(), state)
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


@app.command("list")
def compact_list(
    all_servers: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show jobs from all servers, not just current",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        "-r",
        help="Refresh job states from server before listing",
    ),
) -> None:
    """List cached compaction jobs.

    Shows compaction jobs that were started via yami.
    Use --refresh to update states from the server.
    """
    ctx = get_context()
    current_uri = ctx.get_uri()

    # Get jobs
    if all_servers:
        jobs = job_cache.get_jobs()
    else:
        jobs = job_cache.get_jobs(uri=current_uri)

    if not jobs:
        print_info("No cached compaction jobs found")
        if not all_servers:
            print_info("Use --all to show jobs from all servers")
        return

    # Optionally refresh states
    if refresh:
        client = ctx.get_client()
        for job in jobs:
            if job.get("uri") == current_uri:
                try:
                    state = client.get_compaction_state(job["job_id"])
                    job["state"] = state
                    job_cache.update_job_state(job["job_id"], current_uri, state)
                except Exception:
                    job["state"] = "Unknown"

    # Output based on format
    if ctx.output in ("json", "yaml"):
        format_output({"jobs": jobs}, ctx.output, title="Compaction Jobs")
    else:
        # Table output
        table = Table(title="Compaction Jobs")
        table.add_column("Job ID", style="cyan")
        table.add_column("Collection", style="green")
        table.add_column("Type")
        table.add_column("State", style="yellow")
        table.add_column("Started")
        if all_servers:
            table.add_column("Server")

        for job in jobs:
            started = job.get("started_at", "")[:19].replace("T", " ")
            row = [
                str(job.get("job_id", "")),
                job.get("collection", ""),
                job.get("type", ""),
                job.get("state", "Unknown"),
                started,
            ]
            if all_servers:
                row.append(job.get("uri", ""))
            table.add_row(*row)

        console.print(table)


@app.command("clean")
def compact_clean(
    all_jobs: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Remove all jobs, not just completed ones",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Clean jobs from all servers",
    ),
) -> None:
    """Clean up cached compaction jobs.

    By default, removes only completed/failed jobs for the current server.
    Use --all to remove all cached jobs.
    Use --force to clean jobs from all servers.
    """
    ctx = get_context()
    uri = None if force else ctx.get_uri()

    if all_jobs:
        count = job_cache.clear_all_jobs(uri=uri)
    else:
        count = job_cache.remove_completed_jobs(uri=uri)

    if count > 0:
        print_success(f"Removed {count} job(s) from cache")
    else:
        print_info("No jobs to clean")
