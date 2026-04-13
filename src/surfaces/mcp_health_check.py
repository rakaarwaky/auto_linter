"""MCP Tool: health_check — full system health report.

Checks:
- Agent lifecycle (uptime, status)
- Adapters (count, names, enabled)
- DesktopCommander transport (latency, protocol)
- Job registry (active, completed, failed)
- File system (config, SKILL.md)
"""
import json
import os
import time


def register_health_check(mcp):
    @mcp.tool()
    async def health_check():
        """Check overall system health: lifecycle, adapters, transport, jobs."""
        result = {
            "status": "healthy",
            "components": {},
        }
        issues = []

        # 1. Agent Lifecycle
        try:
            from agent.dependency_injection_container import get_container
            container = get_container()
            lifecycle = container.health()
            result["components"]["agent"] = {
                "status": "healthy",
                "state": lifecycle.get("lifecycle", {}).get("status", "unknown"),
                "uptime_seconds": lifecycle.get("lifecycle", {}).get("uptime_seconds", 0),
                "adapter_count": lifecycle.get("adapter_count", 0),
                "adapters": lifecycle.get("adapters", []),
            }
        except Exception as e:
            result["components"]["agent"] = {"status": "error", "error": str(e)}
            issues.append("agent: " + str(e))

        # 2. DesktopCommander Transport
        try:
            from surfaces.mcp_desktop_client import _get_client
            client = _get_client()
            dc_result = await client.health_check()
            result["components"]["desktop_commander"] = {
                "status": dc_result.get("status", "unknown"),
                "protocol": client.protocol or "Unknown",
                "latency_ms": dc_result.get("latency_ms", 0),
            }
            if dc_result.get("status") != "healthy":
                issues.append("desktop_commander: " + dc_result.get("status", "unknown"))
        except Exception as e:
            result["components"]["desktop_commander"] = {"status": "error", "error": str(e)}
            issues.append("desktop_commander: " + str(e))

        # 3. Job Registry
        try:
            from agent.tracking_job_registry import list_jobs
            jobs = list_jobs()
            total = len(jobs)
            running = sum(1 for j in jobs.values() if j.get("status") == "running")
            completed = sum(1 for j in jobs.values() if j.get("status") == "completed")
            failed = sum(1 for j in jobs.values() if j.get("status") == "failed")
            result["components"]["jobs"] = {
                "status": "healthy",
                "total": total,
                "running": running,
                "completed": completed,
                "failed": failed,
            }
        except Exception as e:
            result["components"]["jobs"] = {"status": "error", "error": str(e)}
            issues.append("jobs: " + str(e))

        # 4. File System Checks
        fs_ok = {}
        skill_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "SKILL.md")
        fs_ok["skill_md"] = os.path.exists(skill_path)

        config_path = os.path.join(os.getcwd(), "auto_linter.config.yaml")
        fs_ok["config"] = os.path.exists(config_path) or os.path.exists(os.path.join(os.getcwd(), ".env"))

        if all(fs_ok.values()):
            result["components"]["filesystem"] = {"status": "healthy", "files": fs_ok}  # pragma: no cover
        else:
            result["components"]["filesystem"] = {"status": "warning", "files": fs_ok}
            missing = [k for k, v in fs_ok.items() if not v]
            issues.append("filesystem missing: " + ", ".join(missing))

        # Overall status
        if issues:
            result["status"] = "degraded" if len(issues) <= 2 else "unhealthy"
        result["issues"] = issues
        result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        return json.dumps(result, indent=2)
