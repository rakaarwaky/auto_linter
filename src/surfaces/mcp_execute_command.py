"""MCP Tool: execute_command - Universal CLI executor via DesktopCommander."""
import json
import os
import shutil
import sys
from datetime import datetime, UTC
from pathlib import Path

from surfaces.mcp_desktop_client import (
    _get_client,
    _execute_with_retry,
)
# Use agent's job tracking - this was previously duplicated here
from agent.tracking_job_registry import create_job, complete_job, fail_job


# Resolve auto-lint binary path at import time
# Priority: venv bin → system PATH
_auto_lint_path = shutil.which("auto-lint", path=os.path.dirname(sys.executable))
if not _auto_lint_path:
    _auto_lint_path = shutil.which("auto-lint")
_auto_lint_cmd = _auto_lint_path or "auto-lint"  # fallback if not installed yet
# Runtime jobs dict for backward compatibility - delegates to agent
_running_jobs: dict = {}


def _track_job(job_id: str, status: str, action: str = ""):
    """Delegate job tracking to agent's registry."""
    _running_jobs[job_id] = {
        "status": status,
        "action": action,
        "started_at": datetime.now(UTC).isoformat(),
    }


def _complete_track_job(job_id: str, result: dict):
    """Mark job as completed in runtime dict."""
    _running_jobs[job_id]["status"] = "completed"
    _running_jobs[job_id]["completed_at"] = datetime.now(UTC).isoformat()
    _running_jobs[job_id]["result"] = result


def _fail_track_job(job_id: str, error: str):
    """Mark job as failed in runtime dict."""
    _running_jobs[job_id]["status"] = "failed"
    _running_jobs[job_id]["completed_at"] = datetime.now(UTC).isoformat()
    _running_jobs[job_id]["result"] = {"error": error}


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
            
            # Find the actual action name from the catalog
            target_action = None
            for candidate in [action, action.replace("_", "-"), action.replace("-", "_")]:
                if candidate in valid_actions:
                    target_action = candidate
                    break

            if not target_action:
                return json.dumps({
                    "error": f"Invalid action '{action}'",
                    "valid_actions_count": len(valid_actions),
                    "suggestion": "Use list_commands() for catalog"
                })
        except Exception as e:
            return json.dumps({"error": f"Failed to validate action: {str(e)}"})

        # Actions that take a positional 'path' argument
        POSITIONAL_PATH_ACTIONS = {
            "check", "scan", "fix", "report", "ci", "batch", "watch",
            "security", "complexity", "duplicates", "trends", "dependencies",
            "suggest", "multi-project"
        }
        
        # Actions that use --path option instead of positional
        OPTIONAL_PATH_ACTIONS = {
            "init", "install-hook", "uninstall-hook", "stats", "ignore"
        }

        # Multi-path commands
        MULTI_PATH_ACTIONS = {"batch", "multi-project"}

        args = args or {}
        # CLI command uses the hyphenated version for the actual call
        cli_cmd = [_auto_lint_cmd, target_action.replace("_", "-")]
        
        # Positional path handling
        if target_action in POSITIONAL_PATH_ACTIONS:
            if target_action in MULTI_PATH_ACTIONS and 'paths' in args:
                paths = args.get('paths')
                if isinstance(paths, list):
                    cli_cmd.extend(paths)
                else:
                    cli_cmd.append(str(paths))
            else:
                path = args.get('path', '.')
                cli_cmd.append(path)
        
        # Optional path or other arguments
        for key, value in args.items():
            if key in ['path', 'paths']:
                if target_action in OPTIONAL_PATH_ACTIONS and key == 'path':
                    cli_cmd.extend([f"--{key.replace('_', '-')}", str(value)])
                # if in POSITIONAL_PATH_ACTIONS, we already added it above
                continue
                
            # Generic option handling
            cli_cmd.extend([f"--{key.replace('_', '-')}", str(value)])

        # Use agent's job tracking - creates proper job in registry
        job_id = await create_job(action)
        _track_job(job_id, "running", action)

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
            # Use agent's job tracking
            await complete_job(job_id, result)
            _complete_track_job(job_id, result)
            result["job_id"] = job_id
            return json.dumps(result)
        except Exception as e:
            client = _get_client()
            # Use agent's job tracking
            await fail_job(job_id, str(e))
            _fail_track_job(job_id, str(e))
            return json.dumps({
                "error": f"Command execution failed: {str(e)}",
                "protocol": client.protocol or "Unknown",
                "job_id": job_id,
            })
