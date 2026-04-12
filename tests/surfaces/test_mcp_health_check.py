"""Tests for MCP health_check tool."""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock
from surfaces.mcp_health_check import register_health_check


class TestHealthCheck:
    def test_register_health_check(self):
        """Test health_check tool is registered."""
        mcp = MagicMock()
        register_health_check(mcp)
        mcp.tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health_check returns success when client is healthy."""
        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value={"status": "ok"})
        mock_client.protocol = "http"

        import surfaces.mcp_desktop_client as dc_module
        dc_module._desktop_commander_client = mock_client

        # Capture the health_check function from registration
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

        register_health_check(mcp)
        result = await tool_func()
        data = json.loads(result)
        assert "status" in data

    @pytest.mark.asyncio
    async def test_health_check_error_handling(self):
        """Test health_check handles errors gracefully."""
        import surfaces.mcp_desktop_client as dc_module
        dc_module._desktop_commander_client = None

        def raise_get_client():
            raise ConnectionError("test error")
        dc_module._get_client = raise_get_client

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

        register_health_check(mcp)
        result = await tool_func()
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_health_check_returns_json(self):
        """Test health_check returns JSON string."""
        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value={"status": "ok", "version": "1.0"})
        mock_client.protocol = "http"

        import surfaces.mcp_desktop_client as dc_module
        dc_module._desktop_commander_client = mock_client

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

        register_health_check(mcp)
        result = await tool_func()
        data = json.loads(result)
        assert "status" in data
        assert isinstance(result, str)
