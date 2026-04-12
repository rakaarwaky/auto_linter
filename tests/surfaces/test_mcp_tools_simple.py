"""Tests for MCP execute_command tool."""

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from surfaces.mcp_execute_command import register_execute_command


class TestExecuteCommand:
    def test_register_execute_command(self):
        """Test execute_command tool is registered."""
        mcp = MagicMock()
        register_execute_command(mcp)
        mcp.tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_empty_action(self):
        """Test execute_command rejects empty action."""
        mcp = MagicMock()
        tool_func = None

        def capture_tool(func=None):
            nonlocal tool_func
            def decorator(f):
                nonlocal tool_func
                tool_func = f
                return f
            if func is None:
                return decorator
            return decorator(func)
        mcp.tool.side_effect = capture_tool

        register_execute_command(mcp)
        result = await tool_func("")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_execute_command_invalid_action(self):
        """Test execute_command rejects invalid action."""
        mcp = MagicMock()
        tool_func = None

        def capture_tool(func=None):
            nonlocal tool_func
            def decorator(f):
                nonlocal tool_func
                tool_func = f
                return f
            if func is None:
                return decorator
            return decorator(func)
        mcp.tool.side_effect = capture_tool

        import surfaces.mcp_execute_command as exec_module
        import surfaces.mcp_command_catalog as catalog_module

        original_list_commands = catalog_module.list_commands
        catalog_module.list_commands = AsyncMock(return_value=json.dumps({"check": {}}))

        register_execute_command(mcp)
        result = await tool_func("nonexistent_command")
        data = json.loads(result)
        assert "error" in data
        assert "Invalid action" in data["error"]

        catalog_module.list_commands = original_list_commands

    @pytest.mark.asyncio
    async def test_execute_command_success(self):
        """Test execute_command with valid action."""
        mcp = MagicMock()
        tool_func = None

        def capture_tool(func=None):
            nonlocal tool_func
            def decorator(f):
                nonlocal tool_func
                tool_func = f
                return f
            if func is None:
                return decorator
            return decorator(func)
        mcp.tool.side_effect = capture_tool

        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(return_value={
            "stdout": "Lint passed", "stderr": "", "exit_code": 0
        })
        mock_client.protocol = "http"

        cmd_catalog = {"check": {"description": "Run lint", "example": "auto-lint check"}}

        with patch("surfaces.mcp_command_catalog.list_commands", return_value=json.dumps(cmd_catalog)):
            with patch("surfaces.mcp_execute_command._get_client", return_value=mock_client):
                with patch("surfaces.mcp_execute_command._execute_with_retry",
                           return_value={"stdout": "Lint passed", "exit_code": 0}):
                    register_execute_command(mcp)
                    result = await tool_func("check", {"path": "/tmp"})
                    data = json.loads(result)
                    assert "job_id" in data

    @pytest.mark.asyncio
    async def test_execute_command_with_args(self):
        """Test execute_command passes args correctly."""
        mcp = MagicMock()
        tool_func = None

        def capture_tool(func=None):
            nonlocal tool_func
            def decorator(f):
                nonlocal tool_func
                tool_func = f
                return f
            if func is None:
                return decorator
            return decorator(func)
        mcp.tool.side_effect = capture_tool

        mock_client = AsyncMock()
        mock_client.protocol = "socket"

        cmd_catalog = {"report": {"description": "Generate report", "example": "auto-lint report"}}

        with patch("surfaces.mcp_command_catalog.list_commands", return_value=json.dumps(cmd_catalog)):
            with patch("surfaces.mcp_execute_command._get_client", return_value=mock_client):
                with patch("surfaces.mcp_execute_command._execute_with_retry",
                           return_value={"stdout": "Report generated", "exit_code": 0}):
                    register_execute_command(mcp)
                    result = await tool_func("report", {"path": "/src", "format": "json"})
                    data = json.loads(result)
                    assert "job_id" in data

    @pytest.mark.asyncio
    async def test_execute_command_hyphenated_action(self):
        """Test execute_command handles hyphenated actions like 'install-hook'."""
        mcp = MagicMock()
        tool_func = None

        def capture_tool(func=None):
            nonlocal tool_func
            def decorator(f):
                nonlocal tool_func
                tool_func = f
                return f
            if func is None:
                return decorator
            return decorator(func)
        mcp.tool.side_effect = capture_tool

        cmd_catalog = {"install-hook": {"description": "Install hook", "example": "auto-lint install-hook"}}

        with patch("surfaces.mcp_command_catalog.list_commands", return_value=json.dumps(cmd_catalog)):
            with patch("surfaces.mcp_execute_command._get_client") as mock_get_client:
                mock_client = AsyncMock()
                mock_client.protocol = "http"
                mock_get_client.return_value = mock_client
                with patch("surfaces.mcp_execute_command._execute_with_retry",
                           return_value={"stdout": "Hook installed", "exit_code": 0}):
                    register_execute_command(mcp)
                    result = await tool_func("install-hook")
                    data = json.loads(result)
                    assert "job_id" in data

    @pytest.mark.asyncio
    async def test_execute_command_exception_handling(self):
        """Test execute_command handles exceptions gracefully."""
        mcp = MagicMock()
        tool_func = None

        def capture_tool(func=None):
            nonlocal tool_func
            def decorator(f):
                nonlocal tool_func
                tool_func = f
                return f
            if func is None:
                return decorator
            return decorator(func)
        mcp.tool.side_effect = capture_tool

        mock_client = AsyncMock()
        mock_client.protocol = "http"

        cmd_catalog = {"check": {"description": "Run lint", "example": "auto-lint check"}}

        with patch("surfaces.mcp_command_catalog.list_commands", return_value=json.dumps(cmd_catalog)):
            with patch("surfaces.mcp_execute_command._get_client", return_value=mock_client):
                with patch("surfaces.mcp_execute_command._execute_with_retry",
                           side_effect=Exception("Connection failed")):
                    register_execute_command(mcp)
                    result = await tool_func("check")
                    data = json.loads(result)
                    assert "error" in data
                    assert "job_id" in data

    @pytest.mark.asyncio
    async def test_execute_command_list_commands_failure(self):
        """Test execute_command handles list_commands failure."""
        mcp = MagicMock()
        tool_func = None

        def capture_tool(func=None):
            nonlocal tool_func
            def decorator(f):
                nonlocal tool_func
                tool_func = f
                return f
            if func is None:
                return decorator
            return decorator(func)
        mcp.tool.side_effect = capture_tool

        with patch("surfaces.mcp_command_catalog.list_commands",
                   side_effect=Exception("Catalog unavailable")):
            register_execute_command(mcp)
            result = await tool_func("check")
            data = json.loads(result)
            assert "error" in data
            assert "Failed to validate" in data["error"]
