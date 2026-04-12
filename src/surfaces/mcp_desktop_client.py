"""MCP tool: DesktopCommander client bridge.

Surface layer delegate to agent for transport.
No direct infrastructure imports — agent owns the connection.
"""
import os
import asyncio
from typing import Any

DESKTOP_COMMANDER_URL = os.environ.get(
    "DESKTOP_COMMANDER_URL",
    "/run/desktop-commander/socket"
)


def _get_client():
    """Get DesktopCommander client from agent container."""
    from agent.dependency_injection_container import get_container
    container = get_container()
    return container.desktop_commander


async def _execute_with_retry(
    client,
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
