"""Unix Domain Socket client for DesktopCommander Communication."""

from __future__ import annotations

import json
import asyncio
import socket
import time
from pathlib import Path
from typing import Any


class UnixSocketClient:
    """Unix Domain Socket protocol client for DesktopCommander."""

    def __init__(self, socket_path: str, timeout: float = 300.0):
        """
        Args:
            socket_path: Path to the Unix domain socket file
            timeout: Connection timeout in seconds
        """
        self.socket_path = socket_path
        self.timeout = timeout
        self._socket: socket.socket | None = None

    def _ensure_socket(self) -> socket.socket:
        """Get or create a connected Unix socket."""
        if self._socket is None or self._socket.fileno() == -1:
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.settimeout(self.timeout)
            resolved = Path(self.socket_path).expanduser().resolve()
            self._socket.connect(str(resolved))
        return self._socket

    def _send_request(self, request_data: dict) -> dict[str, Any]:
        """Send request and receive response via Unix socket (blocking)."""
        try:
            sock = self._ensure_socket()
            request_json = (json.dumps(request_data) + "\n").encode("utf-8")
            sock.sendall(request_json)

            response_data = b""
            sock.settimeout(self.timeout)
            
            # Read until we have a complete JSON object
            # For simplicity, we assume one JSON object per response
            while True:
                try:
                    chunk = sock.recv(8192)
                    if not chunk:
                        break
                    response_data += chunk
                    
                    # Optimization: Only try to parse if it looks like it might be finished
                    # (ends with newline or closing brace)
                    stripped = response_data.strip()
                    if stripped.endswith(b"}"):
                        try:
                            return json.loads(stripped.decode("utf-8"))
                        except json.JSONDecodeError:
                            # Still incomplete or nested braces, keep reading
                            pass
                except socket.timeout:
                    # If we have some data, try to parse it before giving up
                    if response_data:
                        break
                    raise

            # Final attempt
            try:
                return json.loads(response_data.decode("utf-8"))
            except json.JSONDecodeError as e:
                return {
                    "stdout": "",
                    "stderr": f"Failed to parse response: {e}. Data received: {len(response_data)} bytes",
                    "returncode": 1,
                    "executed_by": "DesktopCommanderMCP",
                    "error": "Invalid response format",
                }
        except socket.error as e:
            # Clear socket on error to force reconnect next time
            if self._socket:
                try:
                    self._socket.close()
                except:
                    pass
                self._socket = None
            return {
                "stdout": "",
                "stderr": f"Socket error: {e}",
                "returncode": 1,
                "executed_by": "DesktopCommanderMCP",
                "error": str(e),
            }

    async def execute(
        self, command: list[str], working_dir: str
    ) -> dict[str, Any]:
        """Execute command via Unix socket (async wrapper around blocking call)."""
        request_data = {
            "command": command,
            "working_dir": str(Path(working_dir).resolve()),
            "timeout": self.timeout,
        }

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._send_request, request_data)
        result["protocol"] = "UnixSocket"
        return result

    async def health_check(self) -> dict[str, Any]:
        """Check Unix socket endpoint health."""
        start = time.time()
        result = await self.execute(["echo", "health"], ".")
        latency_ms = (time.time() - start) * 1000
        if result.get("returncode") == 0:
            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "protocol": "UnixSocket",
                "socket_path": self.socket_path,
            }
        return {
            "status": "unhealthy",
            "error": result.get("stderr", "Unknown error"),
            "protocol": "UnixSocket",
            "socket_path": self.socket_path,
        }

    def close(self):
        """Close Unix socket connection."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
                self._socket = None
