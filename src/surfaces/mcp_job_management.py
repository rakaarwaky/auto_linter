"""MCP Tools: check_status and cancel_job."""
import json

# Shared job state from canonical source (mcp_desktop_client)
from surfaces.mcp_desktop_client import _running_jobs


def register_check_status(mcp):
    @mcp.tool()
    async def check_status(job_id: str | None = None):
        """Check status of long-running lint jobs."""
        if job_id is None:
            jobs_list = [
                {"job_id": jid, "status": info["status"], "action": info["action"]}
                for jid, info in _running_jobs.items()
            ]
            return json.dumps({"jobs": jobs_list, "total": len(jobs_list)})
        if job_id not in _running_jobs:
            return json.dumps({"error": f"Job '{job_id}' not found", "status": "not_found"})
        job_info = _running_jobs[job_id]
        return json.dumps({
            "job_id": job_id,
            "status": job_info["status"],
            "action": job_info["action"],
            "started_at": job_info.get("started_at"),
            "completed_at": job_info.get("completed_at"),
            "result": job_info.get("result")
        })


def register_cancel_job(mcp):
    @mcp.tool()
    async def cancel_job(job_id: str):
        """Cancel a running lint job."""
        if job_id not in _running_jobs:
            return json.dumps({"error": f"Job '{job_id}' not found", "status": "not_found"})
        job_info = _running_jobs[job_id]
        if job_info["status"] in ("completed", "failed", "cancelled"):
            return json.dumps({
                "job_id": job_id,
                "status": "already_finished",
                "message": f"Job already {job_info['status']}"
            })
        _running_jobs[job_id]["status"] = "cancelled"
        _running_jobs[job_id]["completed_at"] = "now"
        return json.dumps({
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        })
