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
