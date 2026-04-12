"""Tests for MCP tools registry."""

import pytest
from unittest.mock import MagicMock
from surfaces.mcp_tools_registry import register_tools


class TestToolsRegistry:
    def test_register_all_tools(self):
        """Test all 5 tools are registered."""
        mcp = MagicMock()
        container = MagicMock()

        register_tools(mcp, container)

        # Should register exactly 5 tools
        assert mcp.tool.call_count == 5

    def test_register_tools_imports(self):
        """Test that register_tools imports all sub-modules."""
        # This test ensures imports don't fail
        from surfaces.mcp_execute_command import register_execute_command
        from surfaces.mcp_command_catalog import register_list_commands, register_read_skill_context
        from surfaces.mcp_job_management import register_check_status
        from surfaces.mcp_health_check import register_health_check

        assert callable(register_execute_command)
        assert callable(register_list_commands)
        assert callable(register_read_skill_context)
        assert callable(register_check_status)
        assert callable(register_health_check)

    def test_register_tools_with_container(self):
        """Test register_tools accepts container parameter."""
        mcp = MagicMock()
        container = MagicMock()
        container.analysis_use_case = MagicMock()

        # Should not raise any exception
        register_tools(mcp, container)

    def test_register_tools_tool_names(self):
        """Test that expected tools are registered."""
        mcp = MagicMock()
        container = MagicMock()

        registered_tools = []

        def track_tool(func=None):
            def decorator(f):
                registered_tools.append(f.__name__)
                return f
            if func is None:
                return decorator
            registered_tools.append(func.__name__)
            return decorator(func)
        mcp.tool.side_effect = track_tool

        register_tools(mcp, container)

        # Should have 5 tools
        assert len(registered_tools) == 5
        # Check for expected tool names
        expected = ["execute_command", "list_commands", "read_skill_context",
                    "check_status", "health_check"]
        for name in expected:
            assert name in registered_tools, f"Tool '{name}' not registered"
