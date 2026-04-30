"""Tests for cli_core_commands.py - targeting 100% coverage."""

import json
from unittest.mock import MagicMock, patch, AsyncMock
import click
from click.testing import CliRunner
from surfaces.cli_core_commands import cli


def test_check_results_not_list():
    """Test check command with results that are not lists (line 67)."""
    mock_container = MagicMock()
    mock_report = MagicMock()
    mock_container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
    mock_container.analysis_use_case.to_dict.return_value = {
        "score": 85.0,
        "ruff": [{"file": "test.py", "line": 1, "code": "E501", "message": "long"}],
        "governance": {"level": "B"},  # not a list - should be skipped
        "summary": {},
        "is_passing": True,
    }
    
    runner = CliRunner()
    with patch("surfaces.cli_core_commands.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["check", "."])
        assert result.exit_code == 0
        assert "governance" not in result.output


def test_scan_results_not_list():
    """Test scan command with results that are not lists (line 130)."""
    mock_container = MagicMock()
    mock_report = MagicMock()
    mock_container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
    mock_container.analysis_use_case.to_dict.return_value = {
        "score": 85.0,
        "ruff": [{"file": "test.py", "line": 1, "code": "E501", "message": "long"}],
        "governance": {"level": "B"},  # not a list - should be skipped
        "summary": {},
        "is_passing": True,
    }
    
    runner = CliRunner()
    with patch("surfaces.cli_core_commands.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["scan", "."])
        assert result.exit_code == 0
        assert "governance" not in result.output


def test_security_with_vulnerabilities():
    """Test security command with bandit vulnerabilities (lines 171-173)."""
    mock_container = MagicMock()
    mock_report = MagicMock()
    mock_container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
    mock_container.analysis_use_case.to_dict.return_value = {
        "score": 70.0,
        "bandit": [
            {"file": "test.py", "line": 10, "code": "B101", "message": "assert used", "severity": "medium"},
            {"file": "test.py", "line": 20, "code": "B201", "message": "flask debug", "severity": "high"},
        ],
    }
    
    runner = CliRunner()
    with patch("surfaces.cli_core_commands.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["security", "."])
        assert result.exit_code == 0
        assert "Found 2 vulnerabilities" in result.output
        assert "B101" in result.output
        assert "B201" in result.output


def test_git_diff_text_format():
    """Test git-diff command with text output (lines 183-214)."""
    mock_container = MagicMock()
    mock_container.get_git_diff.return_value = {
        "added": ["src/new.py"],
        "modified": ["src/existing.py"],
        "deleted": ["src/old.py"],
        "renamed": [{"old": "src/a.py", "new": "src/b.py"}],
        "lintable_files": ["src/new.py", "src/existing.py"],
        "all_files": ["src/new.py", "src/existing.py", "src/old.py"],
    }
    
    runner = CliRunner()
    with patch("surfaces.cli_core_commands.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["git-diff"])
        assert result.exit_code == 0
        assert "Added" in result.output
        assert "Modified" in result.output
        assert "Deleted" in result.output
        assert "Renamed" in result.output


def test_git_diff_json_format():
    """Test git-diff command with JSON output (line 196)."""
    mock_container = MagicMock()
    diff_data = {
        "added": ["src/new.py"],
        "modified": ["src/existing.py"],
        "deleted": [],
        "renamed": [],
        "lintable_files": ["src/new.py", "src/existing.py"],
        "all_files": ["src/new.py", "src/existing.py"],
    }
    mock_container.get_git_diff.return_value = diff_data
    
    runner = CliRunner()
    with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["git-diff", "--output-format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "added" in data


def test_git_diff_no_files():
    """Test git-diff command with no changed files (lines 199-200)."""
    mock_container = MagicMock()
    mock_container.get_git_diff.return_value = {
        "added": [],
        "modified": [],
        "deleted": [],
        "renamed": [],
        "lintable_files": [],
        "all_files": [],
    }
    
    runner = CliRunner()
    with patch("surfaces.cli_core_commands.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["git-diff"])
        assert result.exit_code == 0
        assert "No changed files" in result.output


def test_git_diff_not_git_repo():
    """Test git-diff command when not a git repo (lines 185-187)."""
    mock_container = MagicMock()
    mock_container.get_git_diff.return_value = None
    
    runner = CliRunner()
    with patch("surfaces.cli_core_commands.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["git-diff"])
        assert result.exit_code == 0
        assert "Not a git repository" in result.output


def test_plugins_with_discovered():
    """Test plugins command with discovered plugins (lines 223-225)."""
    mock_container = MagicMock()
    mock_plugin = MagicMock()
    mock_plugin.__module__ = "my_module"
    mock_plugin.__name__ = "MyPlugin"
    mock_container.get_discovered_plugins.return_value = {"my_plugin": mock_plugin}
    mock_container.get_custom_adapters.return_value = []
    
    runner = CliRunner()
    with patch("surfaces.cli_core_commands.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["plugins"])
        assert result.exit_code == 0
        assert "Discovered Plugins" in result.output
        assert "my_plugin" in result.output


def test_plugins_with_custom_adapters():
    """Test plugins command with custom adapters (lines 234-237)."""
    mock_container = MagicMock()
    mock_container.get_discovered_plugins.return_value = {}
    mock_container.get_custom_adapters.return_value = [
        {"name": "custom_adapter", "class": "my_module.CustomAdapter"}
    ]
    
    runner = CliRunner()
    with patch("surfaces.cli_core_commands.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["plugins"])
        assert result.exit_code == 0
        assert "Registered Custom Adapters" in result.output
        assert "custom_adapter" in result.output


def test_plugins_no_plugins():
    """Test plugins command with no plugins (lines 246-250)."""
    mock_container = MagicMock()
    mock_container.get_discovered_plugins.return_value = {}
    mock_container.get_custom_adapters.return_value = []
    
    runner = CliRunner()
    with patch("surfaces.cli_core_commands.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["plugins"])
        assert result.exit_code == 0
        assert "No plugins or custom adapters found" in result.output


def test_multi_project_with_paths():
    """Test multi-project command with explicit paths (lines 258-268)."""
    mock_container = MagicMock()
    mock_report = MagicMock()
    mock_report.to_text.return_value = "Multi-project report"
    mock_container.multi_project.scan_all_projects = AsyncMock(return_value=mock_report)
    
    # Mock the module that's imported inside the function
    import sys
    mock_module = MagicMock()
    mock_module.load_multi_project_config = MagicMock(return_value=None)
    sys.modules["agent.multi_project_orchestrator"] = mock_module
    
    runner = CliRunner()
    with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["multi-project", "."])
        assert result.exit_code == 0
        assert "Multi-project report" in result.output


def test_multi_project_json_format():
    """Test multi-project command with JSON output (line 264)."""
    mock_container = MagicMock()
    mock_report = MagicMock()
    mock_report.to_dict.return_value = {"summary": "ok", "projects": 2}
    mock_container.multi_project.scan_all_projects = AsyncMock(return_value=mock_report)
    
    # Mock the module that's imported inside the function
    import sys
    mock_module = MagicMock()
    mock_module.load_multi_project_config = MagicMock(return_value=None)
    sys.modules["agent.multi_project_orchestrator"] = mock_module
    
    runner = CliRunner()
    with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["multi-project", ".", "--output-format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "summary" in data


def test_multi_project_from_config():
    """Test multi-project command loading from config (lines 255-257)."""
    mock_container = MagicMock()
    mock_report = MagicMock()
    mock_report.to_text.return_value = "From config"
    mock_container.multi_project.scan_all_projects = AsyncMock(return_value=mock_report)
    
    # Mock the module that's imported inside the function
    import sys
    mock_module = MagicMock()
    mock_module.load_multi_project_config = MagicMock(return_value=["/path1", "/path2"])
    sys.modules["agent.multi_project_orchestrator"] = mock_module
    
    runner = CliRunner()
    with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
        result = runner.invoke(cli, ["multi-project", "--config", "config.json"])
        assert result.exit_code == 0
        assert "From config" in result.output