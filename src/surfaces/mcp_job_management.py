"""MCP Tool: check_status (cancel_job moved to CLI: auto-lint cancel)."""
import json

# Shared job state from canonical source (mcp_execute_command)
from surfaces.mcp_execute_command import _running_jobs


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
