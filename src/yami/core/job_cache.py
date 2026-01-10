"""Compaction job cache management."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# Cache file location
CACHE_DIR = Path.home() / ".yami"
JOBS_FILE = CACHE_DIR / "compact_jobs.json"


def _ensure_cache_dir() -> None:
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _load_jobs() -> list[dict[str, Any]]:
    """Load jobs from cache file."""
    if not JOBS_FILE.exists():
        return []
    try:
        data = json.loads(JOBS_FILE.read_text())
        return data.get("jobs", [])
    except (json.JSONDecodeError, KeyError):
        return []


def _save_jobs(jobs: list[dict[str, Any]]) -> None:
    """Save jobs to cache file."""
    _ensure_cache_dir()
    JOBS_FILE.write_text(json.dumps({"jobs": jobs}, indent=2))


def add_job(
    job_id: int,
    collection: str,
    compact_type: str,
    uri: str,
) -> None:
    """Add a compaction job to the cache.

    Args:
        job_id: The compaction job ID.
        collection: The collection name.
        compact_type: Type of compaction (default/clustering/l0).
        uri: The Milvus server URI.
    """
    jobs = _load_jobs()

    # Check if job already exists
    for job in jobs:
        if job.get("job_id") == job_id and job.get("uri") == uri:
            return

    jobs.append({
        "job_id": job_id,
        "collection": collection,
        "type": compact_type,
        "uri": uri,
        "started_at": datetime.now().isoformat(),
        "state": "Executing",
    })
    _save_jobs(jobs)


def update_job_state(job_id: int, uri: str, state: str) -> None:
    """Update the state of a cached job.

    Args:
        job_id: The compaction job ID.
        uri: The Milvus server URI.
        state: The new state.
    """
    jobs = _load_jobs()
    for job in jobs:
        if job.get("job_id") == job_id and job.get("uri") == uri:
            job["state"] = state
            job["updated_at"] = datetime.now().isoformat()
            break
    _save_jobs(jobs)


def get_jobs(uri: str | None = None) -> list[dict[str, Any]]:
    """Get all cached jobs, optionally filtered by URI.

    Args:
        uri: Optional URI to filter jobs.

    Returns:
        List of job dictionaries.
    """
    jobs = _load_jobs()
    if uri:
        jobs = [j for j in jobs if j.get("uri") == uri]
    return jobs


def remove_job(job_id: int, uri: str) -> bool:
    """Remove a job from the cache.

    Args:
        job_id: The compaction job ID.
        uri: The Milvus server URI.

    Returns:
        True if job was removed, False if not found.
    """
    jobs = _load_jobs()
    original_len = len(jobs)
    jobs = [j for j in jobs if not (j.get("job_id") == job_id and j.get("uri") == uri)]
    if len(jobs) < original_len:
        _save_jobs(jobs)
        return True
    return False


def remove_completed_jobs(uri: str | None = None) -> int:
    """Remove all completed jobs from the cache.

    Args:
        uri: Optional URI to filter which jobs to clean.

    Returns:
        Number of jobs removed.
    """
    jobs = _load_jobs()
    original_len = len(jobs)

    def should_keep(job: dict[str, Any]) -> bool:
        if uri and job.get("uri") != uri:
            return True
        return job.get("state") not in ("Completed", "Failed")

    jobs = [j for j in jobs if should_keep(j)]
    _save_jobs(jobs)
    return original_len - len(jobs)


def clear_all_jobs(uri: str | None = None) -> int:
    """Clear all jobs from the cache.

    Args:
        uri: Optional URI to filter which jobs to clear.

    Returns:
        Number of jobs removed.
    """
    jobs = _load_jobs()
    original_len = len(jobs)

    if uri:
        jobs = [j for j in jobs if j.get("uri") != uri]
    else:
        jobs = []

    _save_jobs(jobs)
    return original_len - len(jobs)
