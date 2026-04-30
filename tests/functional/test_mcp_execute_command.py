"""Tests for MCP execute command."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import json
from surfaces.mcp_execute_command import register_execute_command


class TestRegisterExecuteCommand:
    def test_register_execute_command(self):
        class MockMCP:
            def __init__(self):
                self.tools = []

            def tool(self):
                def decorator(fn):
                    self.tools.append(fn)
                    return fn
                return decorator

        mock_mcp = MockMCP()
        register_execute_command(mock_mcp)
        assert len(mock_mcp.tools) == 1

    @pytest.mark.asyncio
    async def test_execute_command_empty_action(self):
        class MockMCP:
            def tool(self):
                def decorator(fn):
                    self._fn = fn
                    return fn
                return decorator

        mock_mcp = MockMCP()
        register_execute_command(mock_mcp)

        result = await mock_mcp._fn(action="")
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_execute_command_invalid_action(self):
        class MockMCP:
            def tool(self):
                def decorator(fn):
                    self._fn = fn
                    return fn
                return decorator

        mock_mcp = MockMCP()
        register_execute_command(mock_mcp)

        result = await mock_mcp._fn(action="nonexistent_action")
        data = json.loads(result)
        assert "error" in data
        assert "Invalid action" in data["error"]

    @pytest.mark.asyncio
    async def test_execute_command_action_validation_failure(self):
        """Test execute_command with action validation failure (line 77)."""
        class MockMCP:
            def tool(self):
                def decorator(fn):
                    self._fn = fn
                    return fn
                return decorator

        mock_mcp = MockMCP()
        register_execute_command(mock_mcp)

        # Test with None action
        result = await mock_mcp._fn(action=None)
        data = json.loads(result)
        assert "error" in data
        assert "non-empty string" in data["error"]

        # Test with non-string action
        result = await mock_mcp._fn(action=123)
        data = json.loads(result)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_execute_command_list_commands_failure(self):
        """Test execute_command when list_commands fails (line 77)."""
        class MockMCP:
            def tool(self):
                def decorator(fn):
                    self._fn = fn
                    return fn
                return decorator

        mock_mcp = MockMCP()
        register_execute_command(mock_mcp)

        with patch("surfaces.mcp_command_catalog.list_commands",
                   side_effect=RuntimeError("catalog error")):
            result = await mock_mcp._fn(action="check")
            data = json.loads(result)
            assert "error" in data
            assert "Failed to validate" in data["error"]
