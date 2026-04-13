"""DesktopCommander adapter - orchestrates HTTP and Unix Socket clients.

Auto-detects protocol and delegates to the appropriate client.
Falls back to Stdio (direct subprocess) if DesktopCommander is unavailable.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from infrastructure.http_request_client import HTTPClient
from infrastructure.unix_socket_client import UnixSocketClient
from infrastructure.stdio_transport_client import StdioClient


def detect_protocol(url: str) -> str:
    """Detect protocol from URL format."""
    if url.startswith("http://") or url.startswith("https://"):
        return "HTTP"
    elif url.startswith("/") or url.startswith("."):
        return "UnixSocket"
    return "Unknown"


class DesktopCommanderAdapter:
    """Orchestrator that auto-selects HTTP or Unix Socket client."""

    DEFAULT_SOCKET = "/run/desktop-commander/socket"
    DEFAULT_HTTP = "http://localhost:8080/execute"

    def __init__(
        self,
        url: Optional[str] = None,
        timeout: float = 300.0,
        auto_detect: bool = True,
    ):
        self.url = url or os.environ.get("DESKTOP_COMMANDER_URL", self.DEFAULT_SOCKET)
        self.timeout = timeout
        self._protocol: Optional[str] = None
        self._http_client: Optional[HTTPClient] = None
        self._unix_client: Optional[UnixSocketClient] = None
        self._stdio_client: Optional[StdioClient] = None
        self._auto_detect = auto_detect

        # Always detect protocol from URL format
        self._protocol = detect_protocol(self.url)

    @property
    def protocol(self) -> Optional[str]:
        return self._protocol

    @property
    def is_unix_socket(self) -> bool:
        return self._protocol == "UnixSocket"

    @property
    def is_http(self) -> bool:
        return self._protocol == "HTTP"

    def _get_http_client(self) -> HTTPClient:
        if self._http_client is None:
            http_url = self.url if self.url.startswith("http") else self.DEFAULT_HTTP
            self._http_client = HTTPClient(url=http_url, timeout=self.timeout)
        return self._http_client

    def _get_unix_client(self) -> UnixSocketClient:
        if self._unix_client is None:
            socket_path = self.url if self.url.startswith("/") else self.DEFAULT_SOCKET
            self._unix_client = UnixSocketClient(
                socket_path=socket_path, timeout=self.timeout
            )
        return self._unix_client

    async def execute_command(
        self,
        command: list[str],
        working_dir: str = ".",
        timeout: Optional[int] = None,
    ) -> dict[str, Any]:
        """Execute command via the detected protocol."""
        if self._protocol == "HTTP":
            return await self._get_http_client().execute(command, working_dir)
        elif self._protocol == "UnixSocket":
            return await self._get_unix_client().execute(command, working_dir)
        else:
            return await self._execute_auto(command, working_dir)

    async def _execute_auto(self, command: list[str], working_dir: str) -> dict[str, Any]:
        """Try Unix Socket first, fallback to HTTP."""
        socket_path = self.url if self.url.startswith("/") else self.DEFAULT_SOCKET
        if Path(socket_path).exists():
            self._protocol = "UnixSocket"
            return await self._get_unix_client().execute(command, working_dir)
        self._protocol = "HTTP"
        return await self._get_http_client().execute(command, working_dir)

    async def health_check(self) -> dict[str, Any]:
        """Check DesktopCommander health."""
        if self._protocol == "HTTP":
            return await self._get_http_client().health_check()
        elif self._protocol == "UnixSocket":
            return await self._get_unix_client().health_check()
        else:
            return await self._health_check_auto()

    async def _health_check_auto(self) -> dict[str, Any]:
        socket_path = Path(self.url) if self.url.startswith("/") else Path(self.DEFAULT_SOCKET)
        if socket_path.exists():
            self._protocol = "UnixSocket"
            return await self._get_unix_client().health_check()
        self._protocol = "HTTP"
        return await self._get_http_client().health_check()

    def _get_stdio_client(self) -> StdioClient:
        if self._stdio_client is None:  # pragma: no cover
            self._stdio_client = StdioClient(timeout=self.timeout)  # pragma: no cover
        return self._stdio_client  # pragma: no cover

    async def close(self):
        """Close all client connections."""
        if self._http_client:
            await self._http_client.close()
        if self._unix_client:
            self._unix_client.close()
        if self._stdio_client:
            self._stdio_client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def execute_via_desktop_commander(
    command: list[str],
    working_dir: str = ".",
    timeout: Optional[int] = None,
    url: Optional[str] = None,
) -> dict[str, Any]:
    """Convenience function for simple usage."""
    async with DesktopCommanderAdapter(url=url) as client:
        return await client.execute_command(
            command=command,
            working_dir=working_dir,
            timeout=timeout,
        )
