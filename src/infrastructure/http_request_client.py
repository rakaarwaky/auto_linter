"""
HTTP Client for DesktopCommander Communication.

Uses httpx for async HTTP requests to DesktopCommander's HTTP endpoint.
"""

from __future__ import annotations
import httpx
from pathlib import Path
from typing import Any, Optional


class HTTPClient:
    """HTTP protocol client for DesktopCommander."""

    def __init__(self, url: str, timeout: float = 300.0):
        """
        Args:
            url: HTTP endpoint (e.g., http://localhost:8080/execute)
            timeout: Request timeout in seconds
        """
        self.url = url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def execute(self, command: list[str], working_dir: str) -> dict[str, Any]:
        """Execute command via HTTP POST."""
        request_data = {
            "command": command,
            "working_dir": str(Path(working_dir).resolve()),
            "timeout": self.timeout,
        }

        try:
            client = await self._ensure_client()
            response = await client.post(
                self.url,
                json=request_data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()

            return {
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "returncode": result.get("returncode", 1),
                "executed_by": "DesktopCommanderMCP",
                "protocol": "HTTP",
            }
        except httpx.TimeoutException:
            raise TimeoutError(f"Command timed out after {self.timeout}s")
        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to DesktopCommander HTTP endpoint: {self.url}. "
                f"Error: {e}"
            )
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "returncode": 1,
                "executed_by": "DesktopCommanderMCP",
                "protocol": "HTTP",
                "error": str(e),
            }

    async def health_check(self) -> dict[str, Any]:
        """Check HTTP endpoint health."""
        import time
        start = time.time()
        try:
            client = await self._ensure_client()
            # Try configurable health endpoint or default to /health
            health_path = os.environ.get("DESKTOP_COMMANDER_HEALTH_PATH", "/health")
            
            # If the URL already ends with /execute, we replace it. 
            # Otherwise, we append the health path.
            if self.url.endswith("/execute"):
                health_url = self.url.replace("/execute", health_path)
            else:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(self.url)
                health_url = urlunparse(parsed._replace(path=health_path))

            response = await client.get(health_url, timeout=5.0)
            if response.status_code == 200:
                latency_ms = (time.time() - start) * 1000
                return {
                    "status": "healthy",
                    "latency_ms": round(latency_ms, 2),
                    "protocol": "HTTP",
                    "endpoint": health_url,
                }
            
            # Fallback to a simple echo command via the execute endpoint
            result = await self.execute(["echo", "health"], ".")
            latency_ms = (time.time() - start) * 1000
            if result.get("returncode") == 0:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency_ms, 2),
                    "protocol": "HTTP",
                    "endpoint": self.url,
                    "method": "echo_fallback"
                }
            return {"status": "unhealthy", "error": f"Health check failed (Status {response.status_code})", "protocol": "HTTP"}
        except Exception as e:
            # Final attempt: try echo via execute if even the GET failed
            try:
                result = await self.execute(["echo", "health"], ".")
                if result.get("returncode") == 0:
                    latency_ms = (time.time() - start) * 1000
                    return {
                        "status": "healthy",
                        "latency_ms": round(latency_ms, 2),
                        "protocol": "HTTP",
                        "endpoint": self.url,
                        "method": "echo_fallback_after_exception"
                    }
            except:
                pass
            
            latency_ms = (time.time() - start) * 1000
            return {"status": "unhealthy", "error": str(e), "latency_ms": round(latency_ms, 2), "protocol": "HTTP"}

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
