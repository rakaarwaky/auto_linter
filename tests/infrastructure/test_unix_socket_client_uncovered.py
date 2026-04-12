"""Additional tests for unix_socket_client to cover lines 115-117."""

import pytest
import socket
import json
from unittest.mock import MagicMock, patch
from infrastructure.unix_socket_client import UnixSocketClient


class TestUnixSocketClientHealthCheckConnectionFail:
    """Test health_check when socket connection fails (lines 115-117)."""

    @pytest.mark.asyncio
    async def test_health_check_socket_connection_error(self):
        """Health check returns unhealthy when socket can't connect."""
        client = UnixSocketClient(socket_path="/nonexistent/socket.sock")

        mock_socket = MagicMock()
        mock_socket.connect.side_effect = ConnectionRefusedError("Connection refused")

        with patch("infrastructure.unix_socket_client.socket.socket", return_value=mock_socket):
            result = await client.health_check()
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert result["protocol"] == "UnixSocket"

    @pytest.mark.asyncio
    async def test_health_check_echo_returns_nonzero(self):
        """Health check returns unhealthy when echo command fails."""
        client = UnixSocketClient(socket_path="/tmp/test.sock")

        mock_socket = MagicMock()
        mock_socket.recv.return_value = json.dumps({
            "stdout": "",
            "returncode": 1,
            "stderr": "echo failed"
        }).encode()

        with patch("infrastructure.unix_socket_client.socket.socket", return_value=mock_socket):
            result = await client.health_check()
            assert result["status"] == "unhealthy"
            assert result.get("error") == "echo failed"
