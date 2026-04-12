"""MCP tool registry - bridges capabilities to the MCP surface layer.

Split into granular modules:
- tools_client.py     - execute_command + retry logic
- tools_catalog.py    - list_commands + read_skill_context
- tools_jobs.py       - check_status + cancel_job
- tools_health.py     - health_check
"""
import json
import os
import asyncio
from pathlib import Path
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP
from agent.dependency_injection_container import Container
from infrastructure.desktop_commander_adapter import DesktopCommanderAdapter

DESKTOP_COMMANDER_URL = os.environ.get(
    "DESKTOP_COMMANDER_URL",
    "/run/desktop-commander/socket"
)

_desktop_commander_client: Optional[DesktopCommanderAdapter] = None
_running_jobs: dict[str, dict] = {}


def _get_client() -> DesktopCommanderAdapter:
    global _desktop_commander_client
    if _desktop_commander_client is None:
        _desktop_commander_client = DesktopCommanderAdapter(
            url=DESKTOP_COMMANDER_URL,
            auto_detect=True
        )
    return _desktop_commander_client


async def _execute_with_retry(
    client: DesktopCommanderAdapter,
    command: list[str],
    working_dir: str,
    timeout: int,
    max_retries: int = 5
) -> dict[str, Any]:
    """Execute command with exponential backoff retry."""
    last_error = None
    base_delay = 0.5

    for attempt in range(max_retries):
        try:
            result = await client.execute_command(
                command=command,
                working_dir=working_dir,
                timeout=timeout
            )
            return result
        except (ConnectionError, TimeoutError, OSError) as e:
            last_error = str(e)
            if attempt >= max_retries - 1:
                return {
                    "error": f"DesktopCommander unavailable after {max_retries} attempts",
                    "last_error": last_error,
                    "suggestion": "Ensure DesktopCommander is running: systemctl status desktop-commander"
                }
            wait_time = base_delay * (2 ** attempt)
            import logging
            logging.warning(
                f"DesktopCommander unavailable. Retrying in {wait_time}s "
                f"(attempt {attempt + 1}/{max_retries}). Error: {last_error}"
            )
            await asyncio.sleep(wait_time)

    return {
        "error": "Unexpected retry loop exit",
        "last_error": last_error
    }
