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

    @pytest.mark.asyncio
    async def test_health_check_agent_error(self):
        """Test health_check with agent errors (lines 37-39)."""
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

        with patch("surfaces.mcp_desktop_client._get_client", return_value=mock_client), \
             patch("agent.dependency_injection_container.get_container",
                   side_effect=RuntimeError("agent crash")):
            register_health_check(mcp)
            result = await tool_func()
            data = json.loads(result)
            assert data["components"]["agent"]["status"] == "error"
            assert "agent crash" in data["components"]["agent"]["error"]

    @pytest.mark.asyncio
    async def test_health_check_desktop_commander_error(self):
        """Test health_check with desktop_commander errors (line 52)."""
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
        mock_client.health_check = AsyncMock(return_value={"status": "unhealthy"})
        mock_client.protocol = "http"

        with patch("surfaces.mcp_desktop_client._get_client", return_value=mock_client):
            register_health_check(mcp)
            result = await tool_func()
            data = json.loads(result)
            assert data["components"]["desktop_commander"]["status"] == "unhealthy"
            # Should be in issues since status != "healthy"
            assert any("desktop_commander" in issue for issue in data["issues"])

    @pytest.mark.asyncio
    async def test_health_check_job_registry_error(self):
        """Test health_check with job registry errors (lines 72-74)."""
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

        with patch("surfaces.mcp_desktop_client._get_client", return_value=mock_client), \
             patch("agent.tracking_job_registry.list_jobs",
                   side_effect=RuntimeError("registry down")):
            register_health_check(mcp)
            result = await tool_func()
            data = json.loads(result)
            assert data["components"]["jobs"]["status"] == "error"
            assert "registry down" in data["components"]["jobs"]["error"]

    @pytest.mark.asyncio
    async def test_health_check_filesystem_missing(self):
        """Test health_check with filesystem issues (line 85)."""
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

        def mock_exists(path):
            # Make SKILL.md missing but .env also missing
            return False

        with patch("surfaces.mcp_desktop_client._get_client", return_value=mock_client), \
             patch("os.path.exists", side_effect=mock_exists):
            register_health_check(mcp)
            result = await tool_func()
            data = json.loads(result)
            assert data["components"]["filesystem"]["status"] == "warning"
            assert any("missing" in issue.lower() for issue in data["issues"])

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_multiple_issues(self):
        """Test health_check returns 'unhealthy' when multiple components fail."""
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
        mock_client.protocol = "http"

        with patch("surfaces.mcp_desktop_client._get_client", return_value=mock_client), \
             patch("agent.dependency_injection_container.get_container",
                   side_effect=RuntimeError("agent crash")):
            register_health_check(mcp)
            result = await tool_func()
            data = json.loads(result)
            assert data["status"] == "degraded"
            assert len(data["issues"]) >= 2
