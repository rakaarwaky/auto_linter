"""MCP Tool: check_status (cancel_job moved to CLI: auto-lint cancel)."""
import json

# Shared job state from canonical source
from agent.tracking_job_registry import list_jobs, get_job


def register_check_status(mcp):
    @mcp.tool()
    async def check_status(job_id: str | None = None):
        """Check status of long-running lint jobs."""
        if job_id is None:
            all_jobs = await list_jobs()
            jobs_list = [
                {"job_id": jid, "status": info["status"], "action": info["action"]}
                for jid, info in all_jobs.items()
            ]
            return json.dumps({"jobs": jobs_list, "total": len(jobs_list)})
        
        job_info = await get_job(job_id)
        if job_info is None:
            return json.dumps({"error": f"Job '{job_id}' not found", "status": "not_found"})
            
        return json.dumps({
            "job_id": job_id,
            "status": job_info["status"],
            "action": job_info["action"],
            "started_at": job_info.get("started_at"),
            "completed_at": job_info.get("completed_at"),
            "result": job_info.get("result")
        })
