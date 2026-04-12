"""Comprehensive tests for surfaces/cli_dev_commands.py."""

import json
import os
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from surfaces.cli_dev_commands import register_dev_commands
from surfaces.cli_core_commands import cli

register_dev_commands(cli)


@pytest.fixture(autouse=True)
def mock_container():
    """Mock the container for all tests."""
    mock = MagicMock()
    mock_report = MagicMock()
    mock_report.results = []
    mock_report.score = 85.0
    mock_report.is_passing = True

    mock.analysis_use_case.execute = AsyncMock(return_value=mock_report)
    mock.analysis_use_case.to_dict = MagicMock(return_value={
        "score": 85.0, "is_passing": True, "summary": {},
    })
    mock.hooks_use_case.install = MagicMock(return_value=True)
    mock.hooks_use_case.uninstall = MagicMock(return_value=True)
    with patch("surfaces.cli_dev_commands.get_container", return_value=mock):
        yield mock


@pytest.fixture
def fixtures_path():
    return os.path.dirname(__file__)


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config file."""
    config = {
        "project_name": "test-project",
        "thresholds": {"score": 80.0, "complexity": 10},
        "adapters": ["ruff", "mypy"],
        "ignored_rules": ["E501"],
    }
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config))
    return config_file


class TestDiffCommand:
    def test_diff_text_format(self, fixtures_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["diff", fixtures_path, fixtures_path])
        assert result.exit_code == 0
        assert "Version Comparison" in result.output
        assert "Difference" in result.output

    def test_diff_json_format(self, fixtures_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["diff", fixtures_path, fixtures_path, "--output-format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "version1" in data
        assert "version2" in data
        assert "difference" in data
        assert "status" in data

    def test_diff_improved_score(self, fixtures_path, mock_container):
        mock_container.analysis_use_case.to_dict.side_effect = [
            {"score": 70.0, "is_passing": True, "summary": {}},
            {"score": 90.0, "is_passing": True, "summary": {}},
        ]
        runner = CliRunner()
        result = runner.invoke(cli, ["diff", fixtures_path, fixtures_path])
        assert result.exit_code == 0
        assert "IMPROVED" in result.output

    def test_diff_declined_score(self, fixtures_path, mock_container):
        mock_container.analysis_use_case.to_dict.side_effect = [
            {"score": 90.0, "is_passing": True, "summary": {}},
            {"score": 70.0, "is_passing": True, "summary": {}},
        ]
        runner = CliRunner()
        result = runner.invoke(cli, ["diff", fixtures_path, fixtures_path])
        assert result.exit_code == 0
        assert "DECLINED" in result.output


class TestSuggestCommand:
    def test_suggest_high_score(self, fixtures_path, mock_container):
        mock_container.analysis_use_case.to_dict.return_value = {
            "score": 100.0, "is_passing": True, "summary": {},
        }
        runner = CliRunner()
        result = runner.invoke(cli, ["suggest", fixtures_path])
        assert result.exit_code == 0
        assert "100.0" in result.output

    def test_suggest_low_score(self, fixtures_path, mock_container):
        mock_container.analysis_use_case.to_dict.return_value = {
            "score": 50.0, "is_passing": False, "summary": {},
        }
        runner = CliRunner()
        result = runner.invoke(cli, ["suggest", fixtures_path])
        assert result.exit_code == 0
        assert "50.0" in result.output
        assert "fix" in result.output

    def test_suggest_with_ai_flag(self, fixtures_path, mock_container):
        mock_container.analysis_use_case.to_dict.return_value = {
            "score": 60.0, "is_passing": False, "summary": {},
        }
        runner = CliRunner()
        result = runner.invoke(cli, ["suggest", fixtures_path, "--ai"])
        assert result.exit_code == 0
        assert "AI suggestions" in result.output


class TestIgnoreCommand:
    def test_add_rule(self, tmp_config):
        runner = CliRunner()
        result = runner.invoke(cli, ["ignore", "W503", "--path", str(tmp_config)])
        assert result.exit_code == 0
        assert "Added" in result.output
        config = json.loads(tmp_config.read_text())
        assert "W503" in config["ignored_rules"]

    def test_remove_rule(self, tmp_config):
        runner = CliRunner()
        result = runner.invoke(cli, ["ignore", "E501", "--remove", "--path", str(tmp_config)])
        assert result.exit_code == 0
        assert "Removed" in result.output
        config = json.loads(tmp_config.read_text())
        assert "E501" not in config["ignored_rules"]

    def test_add_duplicate_rule(self, tmp_config):
        runner = CliRunner()
        result = runner.invoke(cli, ["ignore", "E501", "--path", str(tmp_config)])
        assert result.exit_code == 0
        assert "already ignored" in result.output

    def test_remove_nonexistent_rule(self, tmp_config):
        runner = CliRunner()
        result = runner.invoke(cli, ["ignore", "NONEXISTENT", "--remove", "--path", str(tmp_config)])
        assert result.exit_code == 0
        assert "not in ignore list" in result.output

    def test_config_not_found(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["ignore", "E501", "--path", "/nonexistent/config.json"])
        assert result.exit_code == 0
        assert "Config file not found" in result.output

    def test_no_ignored_rules_key(self, tmp_path):
        config = {"project_name": "test"}
        config_file = tmp_path / "minimal_config.json"
        config_file.write_text(json.dumps(config))
        runner = CliRunner()
        result = runner.invoke(cli, ["ignore", "E501", "--path", str(config_file)])
        assert result.exit_code == 0
        assert "Added" in result.output
        config = json.loads(config_file.read_text())
        assert "E501" in config["ignored_rules"]


class TestConfigCommand:
    def test_config_show(self, tmp_config):
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show", "--path", str(tmp_config)])
        assert result.exit_code == 0
        assert "test-project" in result.output

    def test_config_show_not_found(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show", "--path", "/nonexistent/config.json"])
        assert result.exit_code == 0
        assert "Config not found" in result.output

    def test_config_reset(self, tmp_path):
        config_file = tmp_path / "reset_config.json"
        config_file.write_text('{"custom": "data"}')
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "reset", "--path", str(config_file)], input="y\n")
        assert result.exit_code == 0
        assert "Reset" in result.output
        config = json.loads(config_file.read_text())
        assert "project_name" in config


class TestExportCommand:
    def test_export_json(self, mock_container):
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "score" in data

    def test_export_json_to_file(self, mock_container, tmp_path):
        output_file = tmp_path / "report.json"
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "json", "-o", str(output_file)])
        assert result.exit_code == 0
        assert "Exported" in result.output
        assert output_file.exists()

    def test_export_sarif(self, mock_container):
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "sarif"])
        # Should run without error
        assert result.exit_code == 0

    def test_export_junit(self, mock_container):
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "junit"])
        assert result.exit_code == 0


class TestInitCommand:
    def test_init_creates_config(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "Initialized" in result.output
        config_file = tmp_path / ".json"
        assert config_file.exists()
        config = json.loads(config_file.read_text())
        assert "project_name" in config
        assert "thresholds" in config
        assert "adapters" in config

    def test_init_overwrite_existing(self, tmp_path):
        config_file = tmp_path / ".json"
        config_file.write_text('{"old": "data"}')
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)], input="y\n")
        assert result.exit_code == 0
        assert "Initialized" in result.output

    def test_init_skip_overwrite(self, tmp_path):
        config_file = tmp_path / ".json"
        config_file.write_text('{"old": "data"}')
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)], input="n\n")
        assert result.exit_code == 0
        config = json.loads(config_file.read_text())
        assert config == {"old": "data"}


class TestInstallHookCommand:
    def test_install_hook_success(self, mock_container):
        mock_container.hooks_use_case.install = MagicMock(return_value=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["install-hook"])
        assert result.exit_code == 0
        assert "installed successfully" in result.output

    def test_install_hook_failure(self, mock_container):
        mock_container.hooks_use_case.install = MagicMock(return_value=False)
        runner = CliRunner()
        result = runner.invoke(cli, ["install-hook"])
        assert result.exit_code == 0
        assert "Failed" in result.output


class TestUninstallHookCommand:
    def test_uninstall_hook_success(self, mock_container):
        mock_container.hooks_use_case.uninstall = MagicMock(return_value=True)
        runner = CliRunner()
        result = runner.invoke(cli, ["uninstall-hook"])
        assert result.exit_code == 0
        assert "removed successfully" in result.output

    def test_uninstall_hook_failure(self, mock_container):
        mock_container.hooks_use_case.uninstall = MagicMock(return_value=False)
        runner = CliRunner()
        result = runner.invoke(cli, ["uninstall-hook"])
        assert result.exit_code == 0
        assert "Failed" in result.output
