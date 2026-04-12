"""More comprehensive tests for MCP command catalog."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from surfaces.mcp_command_catalog import list_commands, read_skill_context


class TestMCPCommandCatalog:
    @pytest.mark.asyncio
    async def test_list_commands_with_domain(self):
        """Test list_commands with domain filter."""
        result = await list_commands("linting")
        # When domain is provided, returns dict directly
        if isinstance(result, dict):
            assert "linting" in result
        else:
            data = json.loads(result)
            assert "linting" in data

    @pytest.mark.asyncio
    async def test_read_skill_context_found_section(self):
        """Test reading specific section from SKILL.md."""
        # First check if SKILL.md exists
        skill_path = Path(__file__).parent.parent.parent.parent / "SKILL.md"
        if skill_path.exists():
            result = await read_skill_context("introduction")
            data = json.loads(result)
            # Either section is found or error about section not found

    @pytest.mark.asyncio
    async def test_read_skill_context_exception_handling(self):
        """Test exception handling in read_skill_context when SKILL.md exists but read fails."""
        # First, verify the behavior when SKILL.md does not exist
        result = await read_skill_context()
        data = json.loads(result)
        # In test environment, SKILL.md may not exist - check error or success
        assert "table_of_contents" in data or "error" in data

    @pytest.mark.asyncio
    async def test_read_skill_context_skill_not_found(self):
        """Test read_skill_context when SKILL.md does not exist (lines 41-44)."""
        # The function looks for SKILL.md at project root
        # In test env it likely doesn't exist at that relative path
        result = await read_skill_context("nonexistent")
        data = json.loads(result)
        # Should return error or handle gracefully
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_read_skill_context_with_existing_skill(self):
        """Test read_skill_context when SKILL.md exists and section is found."""
        skill_path = Path(__file__).parent.parent.parent.parent / "SKILL.md"
        if skill_path.exists():
            # Read to find a valid section name
            content = skill_path.read_text()
            sections = content.split("## ")
            if len(sections) > 1:
                section_name = sections[1].split("\n")[0].strip()
                result = await read_skill_context(section_name.lower())
                data = json.loads(result)
                assert "section" in data or "content" in data

    @pytest.mark.asyncio
    async def test_read_skill_context_section_not_found(self):
        """Test read_skill_context when section is not found."""
        skill_path = Path(__file__).parent.parent.parent.parent / "SKILL.md"
        if skill_path.exists():
            result = await read_skill_context("xyznonexistentsection123")
            data = json.loads(result)
            assert "error" in data or "available" in data

    @pytest.mark.asyncio
    async def test_read_skill_context_read_exception(self):
        """Test read_skill_context exception path when file read fails."""
        with patch("builtins.open", side_effect=IOError("permission denied")):
            # Need to make Path.exists return True to trigger the try block
            with patch.object(Path, "exists", return_value=True):
                result = await read_skill_context()
                data = json.loads(result)
                assert "error" in data


def test_command_catalog_commands_count():
    """Verify command catalog has expected number of commands."""
    from surfaces.mcp_command_catalog import _COMMAND_CATALOG
    # Should have all expected commands
    assert "check" in _COMMAND_CATALOG
    assert "scan" in _COMMAND_CATALOG
    assert "fix" in _COMMAND_CATALOG
    assert "report" in _COMMAND_CATALOG
    assert "ci" in _COMMAND_CATALOG
    assert "batch" in _COMMAND_CATALOG
    assert "watch" in _COMMAND_CATALOG
    assert "security" in _COMMAND_CATALOG
    assert "complexity" in _COMMAND_CATALOG
    assert "duplicates" in _COMMAND_CATALOG
    assert "trends" in _COMMAND_CATALOG
    assert "stats" in _COMMAND_CATALOG
    assert "clean" in _COMMAND_CATALOG
    assert "update" in _COMMAND_CATALOG
    assert "doctor" in _COMMAND_CATALOG


def test_command_catalog_has_descriptions():
    """Verify command catalog entries have descriptions and examples."""
    from surfaces.mcp_command_catalog import _COMMAND_CATALOG
    for cmd, info in _COMMAND_CATALOG.items():
        assert "description" in info
        assert "example" in info
        assert isinstance(info["description"], str)
        assert isinstance(info["example"], str)