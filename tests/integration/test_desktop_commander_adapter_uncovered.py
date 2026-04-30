"""Additional tests for desktop_commander_adapter to cover remaining uncovered lines."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.infrastructure.desktop_commander_adapter import (
    DesktopCommanderAdapter, detect_protocol
)


class TestDesktopCommanderAdapterUnknownProtocol:
    """Tests for unknown protocol paths (lines 94-95, 117-119)."""

    @pytest.mark.asyncio
    async def test_execute_command_unknown_protocol_calls_execute_auto(self):
        """When protocol is Unknown, execute_command calls _execute_auto."""
        adapter = DesktopCommanderAdapter(url="unknown")
        # Protocol should be "Unknown"
        assert adapter._protocol == "Unknown"
        
        mock_result = {"result": "auto", "protocol": "UnixSocket"}
        adapter._execute_auto = AsyncMock(return_value=mock_result)

        result = await adapter.execute_command(["echo", "hello"])
        assert result == mock_result
        adapter._execute_auto.assert_called_once_with(["echo", "hello"], ".")

    @pytest.mark.asyncio
    async def test_health_check_unknown_protocol_calls_health_check_auto(self):
        """When protocol is Unknown, health_check calls _health_check_auto."""
        adapter = DesktopCommanderAdapter(url="unknown")
        assert adapter._protocol == "Unknown"

        mock_result = {"status": "healthy", "protocol": "HTTP"}
        adapter._health_check_auto = AsyncMock(return_value=mock_result)

        result = await adapter.health_check()
        assert result == mock_result
        adapter._health_check_auto.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_auto_unix_socket_exists(self, tmp_path):
        """_execute_auto: socket exists -> uses UnixSocket (lines 94-95)."""
        sock = tmp_path / "dc.sock"
        sock.touch()

        adapter = DesktopCommanderAdapter(url=str(sock))
        mock_unix = AsyncMock()
        mock_unix.execute = AsyncMock(return_value={"result": "unix"})
        adapter._unix_client = mock_unix

        result = await adapter._execute_auto(["echo", "hello"], ".")
        assert result == {"result": "unix"}
        assert adapter._protocol == "UnixSocket"

    @pytest.mark.asyncio
    async def test_execute_auto_unix_socket_not_exists_fallback_http(self, tmp_path):
        """_execute_auto: socket doesn't exist -> fallback to HTTP."""
        non_existent = str(tmp_path / "nonexistent.sock")
        adapter = DesktopCommanderAdapter(url=non_existent)
        mock_http = AsyncMock()
        mock_http.execute = AsyncMock(return_value={"result": "http"})
        adapter._http_client = mock_http

        result = await adapter._execute_auto(["echo", "hello"], ".")
        assert result == {"result": "http"}
        assert adapter._protocol == "HTTP"

    @pytest.mark.asyncio
    async def test_health_check_auto_socket_exists(self, tmp_path):
        """_health_check_auto: socket exists -> uses UnixSocket (lines 117-119)."""
        sock = tmp_path / "dc.sock"
        sock.touch()

        adapter = DesktopCommanderAdapter(url=str(sock))
        mock_unix = AsyncMock()
        mock_unix.health_check = AsyncMock(return_value={"status": "healthy_unix"})
        adapter._unix_client = mock_unix

        result = await adapter._health_check_auto()
        assert result == {"status": "healthy_unix"}
        assert adapter._protocol == "UnixSocket"

    @pytest.mark.asyncio
    async def test_health_check_auto_socket_doesnt_exist_falls_back_to_http(self, tmp_path):
        """_health_check_auto when socket doesn't exist falls back to HTTP."""
        non_existent = str(tmp_path / "nonexistent.sock")
        adapter = DesktopCommanderAdapter(url=non_existent)
        
        # Mock HTTP client health check
        mock_http = AsyncMock()
        mock_http.health_check = AsyncMock(return_value={
            "status": "healthy",
            "protocol": "HTTP",
        })
        adapter._http_client = mock_http

        result = await adapter._health_check_auto()
        assert result["status"] == "healthy"
        assert result["protocol"] == "HTTP"
        # Protocol should have been switched to HTTP
        assert adapter._protocol == "HTTP"
