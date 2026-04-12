"""Auto-Linter MCP Tools Tests - Token Efficiency Optimized (5 core tools)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock
from surfaces.mcp_tools_registry import register_tools


def test_register_tools():
    """Test that core tools are registered after optimization."""
    mcp = MagicMock()
    container = MagicMock()

    register_tools(mcp, container)

    # Verify: 5 core tools (execute_command, list_commands, read_skill_context,
    # check_status, health_check)
    assert mcp.tool.call_count == 5

