"""MCP Tool: execute_command - Universal CLI executor via DesktopCommander."""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from surfaces.mcp_desktop_client import (
    _get_client,
    _execute_with_retry,
    _running_jobs,
)


def register_execute_command(mcp):
    """Register the execute_command MCP tool."""

    @mcp.tool()
    async def execute_command(action: str, args: dict | None = None):
        """Execute ANY CLI command via DesktopCommanderMCP.

        Core of hybrid architecture pattern. Supports all 25+ CLI commands.

        Args:
            action: Command name (check, fix, report, diff, suggest, etc.)
            args: Optional command arguments (path, format, options)

        Returns:
            JSON with command output from DesktopCommander
        """
        if not action or not isinstance(action, str):
            return json.dumps({"error": "Action must be a non-empty string"})

        # Import list_commands locally to avoid circular imports
        from surfaces.mcp_command_catalog import list_commands

        try:
            cmd_catalog = await list_commands()
            if isinstance(cmd_catalog, str):
                commands_dict = json.loads(cmd_catalog)
            else:
                commands_dict = dict(cmd_catalog)

            valid_actions = set(commands_dict.keys())
            normalized_action = action.replace("-", "_")

            if action not in valid_actions and normalized_action not in valid_actions:
                return json.dumps({
                    "error": f"Invalid action '{action}'",
                    "valid_actions_count": len(valid_actions),
                    "suggestion": "Use list_commands() for catalog"
                })
        except Exception as e:
            return json.dumps({"error": f"Failed to validate action: {str(e)}"})

        args = args or {}
        path = args.get('path', '.')
        cli_cmd = ["auto-lint", normalized_action, path]

        for key, value in args.items():
            if key != 'path':
                cli_cmd.extend([f"--{key}", str(value)])

        job_id = str(uuid.uuid4())[:8]
        _running_jobs[job_id] = {
            "status": "running",
            "action": action,
            "started_at": datetime.utcnow().isoformat(),
        }

        try:
            client = _get_client()
            result = await _execute_with_retry(
                client=client,
                command=cli_cmd,
                working_dir=str(Path.cwd()),
                timeout=300,
                max_retries=5
            )

            if "protocol" not in result:
                result["protocol"] = client.protocol or "Unknown"
            _running_jobs[job_id]["status"] = "completed"
            _running_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
            _running_jobs[job_id]["result"] = result
            result["job_id"] = job_id
            return json.dumps(result)
        except Exception as e:
            client = _get_client()
            _running_jobs[job_id]["status"] = "failed"
            _running_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
            _running_jobs[job_id]["result"] = {"error": str(e)}
            return json.dumps({
                "error": f"Command execution failed: {str(e)}",
                "protocol": client.protocol or "Unknown",
                "job_id": job_id,
            })
