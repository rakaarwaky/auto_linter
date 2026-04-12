"""Stdio transport — direct subprocess execution, no DesktopCommander needed."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any


class StdioClient:
    """Direct subprocess transport. Runs commands locally without any intermediary."""

    def __init__(self, timeout: float = 300.0):
        self.timeout = timeout

    async def execute(self, command: list[str], working_dir: str) -> dict[str, Any]:
        """Execute command via subprocess and capture output."""
        resolved_dir = str(Path(working_dir).resolve())

        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=resolved_dir,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return {
                    "stdout": "",
                    "stderr": f"Command timed out after {self.timeout}s",
                    "returncode": -1,
                    "protocol": "Stdio",
                    "error": "timeout",
                }

            return {
                "stdout": stdout_bytes.decode("utf-8", errors="replace"),
                "stderr": stderr_bytes.decode("utf-8", errors="replace"),
                "returncode": proc.returncode,
                "protocol": "Stdio",
            }

        except FileNotFoundError:
            return {
                "stdout": "",
                "stderr": f"Command not found: {command[0]}",
                "returncode": 127,
                "protocol": "Stdio",
                "error": "command_not_found",
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": 1,
                "protocol": "Stdio",
                "error": str(e),
            }

    async def health_check(self) -> dict[str, Any]:
        """Stdio is always healthy if Python is running."""
        import time
        start = time.time()
        result = await self.execute(["echo", "health"], ".")
        latency_ms = (time.time() - start) * 1000

        if result.get("returncode") == 0:
            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "protocol": "Stdio",
                "pid": os.getpid(),
            }
        return {
            "status": "unhealthy",
            "error": result.get("stderr", "Unknown"),
            "protocol": "Stdio",
        }

    def close(self):
        """No resources to clean up for stdio."""
        pass
