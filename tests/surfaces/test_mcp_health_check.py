"""Tests for MCP health_check tool."""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from surfaces.mcp_health_check import register_health_check


class TestHealthCheck:
    def test_register_health_check(self):
        """Test health_check tool is registered."""
        mcp = MagicMock()
        register_health_check(mcp)
        mcp.tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health_check returns success when healthy."""
        mcp = MagicMock()
        tool_func = None

        def capture_decorator(func=None):
            nonlocal tool_func
            def decorator(f):
                nonlocal tool_func
                tool_func = f
                return f
            if func is None:
                return decorator
            return decorator(func)
        mcp.tool.side_effect = capture_decorator

        # Mock desktop client
        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value={
            "status": "healthy", "latency_ms": 2.0
        })
        mock_client.protocol = "UnixSocket"

        with patch("surfaces.mcp_desktop_client._get_client", return_value=mock_client):
            register_health_check(mcp)
            result = await tool_func()
            data = json.loads(result)
            assert "components" in data
            assert "agent" in data["components"]
            assert "desktop_commander" in data["components"]
            assert "jobs" in data["components"]

    @pytest.mark.asyncio
    async def test_health_check_degraded(self):
        """Test health_check reports degraded when components fail."""
        mcp = MagicMock()
        tool_func = None

        def capture_decorator(func=None):
            nonlocal tool_func
            def decorator(f):
                nonlocal tool_func
                tool_func = f
                return f
            if func is None:
                return decorator
            return decorator(func)
        mcp.tool.side_effect = capture_decorator

        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(side_effect=ConnectionError("dc down"))
        mock_client.protocol = "Unknown"

        with patch("surfaces.mcp_desktop_client._get_client", return_value=mock_client):
            register_health_check(mcp)
            result = await tool_func()
            data = json.loads(result)
            assert data["status"] in ("degraded", "unhealthy")
            assert len(data["issues"]) > 0
            assert "components" in data

    @pytest.mark.asyncio
    async def test_health_check_returns_json(self):
        """Test health_check returns JSON string."""
        mcp = MagicMock()
        tool_func = None

        def capture_decorator(func=None):
            nonlocal tool_func
            def decorator(f):
                nonlocal tool_func
                tool_func = f
                return f
            if func is None:
                return decorator
            return decorator(func)
        mcp.tool.side_effect = capture_decorator

        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_client.protocol = "http"

        with patch("surfaces.mcp_desktop_client._get_client", return_value=mock_client):
            register_health_check(mcp)
            result = await tool_func()
            assert isinstance(result, str)
            data = json.loads(result)
            assert "status" in data
