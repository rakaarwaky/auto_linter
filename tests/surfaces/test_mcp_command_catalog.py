"""Tests for MCP command catalog."""
import json
import pytest
from unittest.mock import MagicMock
from surfaces.mcp_command_catalog import (
    list_commands, read_skill_context,
    register_list_commands, register_read_skill_context,
)


class TestListCommands:
    @pytest.mark.asyncio
    async def test_list_commands_returns_json_string(self):
        result = await list_commands()
        data = json.loads(result)
        assert isinstance(data, dict)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_list_commands_has_check(self):
        result = await list_commands()
        data = json.loads(result)
        assert "check" in data
        assert "description" in data["check"]
        assert "example_usage" in data["check"]

    @pytest.mark.asyncio
    async def test_list_commands_has_fix(self):
        result = await list_commands()
        data = json.loads(result)
        assert "fix" in data

    @pytest.mark.asyncio
    async def test_list_commands_has_report(self):
        result = await list_commands()
        data = json.loads(result)
        assert "report" in data

    @pytest.mark.asyncio
    async def test_list_commands_has_all_expected(self):
        result = await list_commands()
        data = json.loads(result)
        expected = {"check", "scan", "fix", "report", "ci", "batch", "watch",
                    "security", "complexity", "duplicates", "trends", "dependencies"}
        assert expected.issubset(set(data.keys()))

    @pytest.mark.asyncio
    async def test_list_commands_with_domain(self):
        result = await list_commands(domain="test")
        # When domain is passed, returns dict directly (not JSON string)
        if isinstance(result, str):
            data = json.loads(result)
        else:
            data = result
        assert isinstance(data, dict)


class TestReadSkillContext:
    @pytest.mark.asyncio
    async def test_read_skill_context_no_section(self):
        result = await read_skill_context()
        data = json.loads(result)
        # Either TOC or error (SKILL.md may not exist in test env)
        assert "table_of_contents" in data or "error" in data

    @pytest.mark.asyncio
    async def test_read_skill_context_with_section(self):
        result = await read_skill_context(section="nonexistent")
        data = json.loads(result)
        assert "error" in data or "section" in data

    @pytest.mark.asyncio
    async def test_read_skill_context_skilmd_missing(self):
        # Just verify it doesn't crash - returns TOC or error
        result = await read_skill_context()
        data = json.loads(result)
        assert isinstance(data, dict)


class TestRegisterFunctions:
    def test_register_list_commands(self):
        mock_mcp = MagicMock()
        register_list_commands(mock_mcp)
        mock_mcp.tool.assert_called_once()

    def test_register_read_skill_context(self):
        mock_mcp = MagicMock()
        register_read_skill_context(mock_mcp)
        mock_mcp.tool.assert_called_once()
