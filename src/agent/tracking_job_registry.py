"""Agent jobs — lifecycle and job tracking."""

from __future__ import annotations
import uuid
import asyncio
import logging
from typing import Any, Callable, Awaitable
from datetime import datetime, timezone

_jobs: dict[str, dict] = {}

logger = logging.getLogger("agent.jobs")


def create_job(action: str) -> str:
    """Register a new job and return its ID."""
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "status": "running",
        "action": action,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    return job_id


def complete_job(job_id: str, result: Any):
    """Mark job as completed."""
    if job_id in _jobs:
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        _jobs[job_id]["result"] = result


def fail_job(job_id: str, error: str):
    """Mark job as failed."""
    if job_id in _jobs:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        _jobs[job_id]["result"] = {"error": error}


def list_jobs() -> dict[str, dict]:
    """Return all jobs."""
    return dict(_jobs)


def get_job(job_id: str) -> dict | None:
    """Return a single job or None."""
    return _jobs.get(job_id)


def cancel_job(job_id: str) -> bool:
    """Cancel a running job. Returns True if cancelled."""
    if job_id not in _jobs:
        return False
    if _jobs[job_id]["status"] not in ("running",):
        return False
    _jobs[job_id]["status"] = "cancelled"
    _jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    return True


async def run_with_retry(
    func: Callable[[], Awaitable[Any]],
    max_retries: int = 5,
    base_delay: float = 0.5,
) -> Any:
    """Execute async function with exponential backoff retry."""
    last_error = None
    for attempt in range(max_retries):
        try:
            return await func()
        except (ConnectionError, TimeoutError, OSError) as e:
            last_error = str(e)
            if attempt >= max_retries - 1:
                raise
            wait_time = base_delay * (2 ** attempt)
            logger.warning(
                "Transient failure, retrying in %.1fs (attempt %d/%d): %s",
                wait_time, attempt + 1, max_retries, last_error,
            )
            await asyncio.sleep(wait_time)
    raise RuntimeError(f"Unexpected retry exit: {last_error}")
