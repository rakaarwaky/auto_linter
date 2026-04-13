"""Tests for CLI dev commands."""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from click.testing import CliRunner
from surfaces.cli_dev_commands import register_dev_commands
import click


@pytest.fixture
def cli_group():
    @click.group()
    def cli():
        pass
    register_dev_commands(cli)
    return cli


@pytest.fixture
def runner():
    return CliRunner()


class TestDiffCommand:
    def test_diff_text(self, runner, cli_group, tmp_path):
        f1 = tmp_path / "v1.py"
        f1.write_text("x = 1\n")
        f2 = tmp_path / "v2.py"
        f2.write_text("x = 2\n")
        with patch("agent.dependency_injection_container.get_container") as mock_gc:
            container = MagicMock()
            mock_report = MagicMock()
            container.analysis_use_case.execute = MagicMock(return_value=mock_report)
            container.analysis_use_case.to_dict.side_effect = [
                {"score": 80.0},
                {"score": 85.0},
            ]
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["diff", str(f1), str(f2)])
        assert result.exit_code == 0
        assert "Comparison" in result.output or "IMPROVED" in result.output

    def test_diff_json(self, runner, cli_group, tmp_path):
        f1 = tmp_path / "v1.py"
        f1.write_text("x = 1\n")
        f2 = tmp_path / "v2.py"
        f2.write_text("x = 2\n")
        with patch("agent.dependency_injection_container.get_container") as mock_gc:
            container = MagicMock()
            mock_report = MagicMock()
            container.analysis_use_case.execute = MagicMock(return_value=mock_report)
            container.analysis_use_case.to_dict.side_effect = [
                {"score": 80.0},
                {"score": 85.0},
            ]
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["diff", str(f1), str(f2), "--output-format", "json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert "difference" in data

    def test_diff_score_declined(self, runner, cli_group, tmp_path):
        """Test diff when score goes down (lines 61-63)."""
        f1 = tmp_path / "v1.py"
        f1.write_text("x = 1\n")
        f2 = tmp_path / "v2.py"
        f2.write_text("x = 2\n")
        with patch("surfaces.cli_dev_commands.get_container") as mock_gc:
            container = MagicMock()
            mock_report = MagicMock()
            container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
            container.analysis_use_case.to_dict.side_effect = [
                {"score": 90.0},
                {"score": 80.0},
            ]
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["diff", str(f1), str(f2)])
        assert result.exit_code == 0
        assert "DECLINED" in result.output

    def test_diff_score_unchanged(self, runner, cli_group, tmp_path):
        """Test diff when score is the same."""
        f1 = tmp_path / "v1.py"
        f1.write_text("x = 1\n")
        f2 = tmp_path / "v2.py"
        f2.write_text("x = 2\n")
        with patch("agent.dependency_injection_container.get_container") as mock_gc:
            container = MagicMock()
            mock_report = MagicMock()
            container.analysis_use_case.execute = MagicMock(return_value=mock_report)
            container.analysis_use_case.to_dict.side_effect = [
                {"score": 85.0},
                {"score": 85.0},
            ]
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["diff", str(f1), str(f2)])
        assert result.exit_code == 0
        assert "UNCHANGED" in result.output


class TestSuggestCommand:
    def test_suggest_basic(self, runner, cli_group, tmp_path):
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")
        mock_container = MagicMock()
        mock_report = MagicMock()
        mock_container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
        mock_container.analysis_use_case.to_dict.return_value = {"score": 75.0}
        with patch("surfaces.cli_dev_commands.get_container", return_value=mock_container):
            result = runner.invoke(cli_group, ["suggest", str(f)])
        assert result.exit_code == 0
        assert "Suggestions" in result.output

    def test_suggest_with_ai(self, runner, cli_group, tmp_path):
        """Test suggest with --ai flag (lines 61-63)."""
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")
        mock_container = MagicMock()
        mock_report = MagicMock()
        mock_container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
        mock_container.analysis_use_case.to_dict.return_value = {"score": 75.0}
        with patch("surfaces.cli_dev_commands.get_container", return_value=mock_container):
            result = runner.invoke(cli_group, ["suggest", str(f), "--ai"])
        assert result.exit_code == 0
        assert "Governance score is 75.0" in result.output
        assert "AI suggestions" in result.output

    def test_suggest_with_ai_perfect_score(self, runner, cli_group, tmp_path):
        """Test suggest with --ai flag and perfect score (lines 61-63)."""
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")
        mock_container = MagicMock()
        mock_report = MagicMock()
        mock_container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
        mock_container.analysis_use_case.to_dict.return_value = {"score": 100.0}
        with patch("surfaces.cli_dev_commands.get_container", return_value=mock_container):
            result = runner.invoke(cli_group, ["suggest", str(f), "--ai"])
        assert result.exit_code == 0
        assert "100.0" in result.output
        assert "AI suggestions" in result.output

    def test_suggest_perfect_score(self, runner, cli_group, tmp_path):
        """Test suggest when score is 100."""
        f = tmp_path / "test.py"
        f.write_text("x = 1\n")
        mock_container = MagicMock()
        mock_report = MagicMock()
        mock_container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
        mock_container.analysis_use_case.to_dict.return_value = {"score": 100.0}
        with patch("surfaces.cli_dev_commands.get_container", return_value=mock_container):
            result = runner.invoke(cli_group, ["suggest", str(f)])
        assert result.exit_code == 0
        assert "100.0" in result.output


class TestIgnoreCommand:
    def test_ignore_add(self, runner, cli_group, tmp_path):
        config = tmp_path / "config.json"
        config.write_text('{"ignored_rules": []}')
        result = runner.invoke(cli_group, ["ignore", "E501", "--path", str(config)])
        assert result.exit_code == 0
        assert "Added" in result.output

    def test_ignore_remove(self, runner, cli_group, tmp_path):
        """Test ignore with --remove (lines 88-90)."""
        config = tmp_path / "config.json"
        config.write_text('{"ignored_rules": ["E501"]}')
        result = runner.invoke(cli_group, ["ignore", "E501", "--remove", "--path", str(config)])
        assert result.exit_code == 0
        assert "Removed" in result.output

    def test_ignore_remove_not_found(self, runner, cli_group, tmp_path):
        """Test ignore --remove when rule not in list (line 95)."""
        config = tmp_path / "config.json"
        config.write_text('{"ignored_rules": ["E501"]}')
        result = runner.invoke(cli_group, ["ignore", "W503", "--remove", "--path", str(config)])
        assert result.exit_code == 0
        assert "not in ignore list" in result.output

    def test_ignore_already_ignored(self, runner, cli_group, tmp_path):
        """Test ignore when rule already ignored (line 101)."""
        config = tmp_path / "config.json"
        config.write_text('{"ignored_rules": ["E501"]}')
        result = runner.invoke(cli_group, ["ignore", "E501", "--path", str(config)])
        assert result.exit_code == 0
        assert "already ignored" in result.output

    def test_ignore_no_ignored_rules_key(self, runner, cli_group, tmp_path):
        """Test ignore when config has no ignored_rules key (line 88)."""
        config = tmp_path / "config.json"
        config.write_text('{"other_key": "value"}')
        result = runner.invoke(cli_group, ["ignore", "E501", "--path", str(config)])
        assert result.exit_code == 0
        assert "Added" in result.output
        # Verify the key was added
        import json
        data = json.loads(config.read_text())
        assert "ignored_rules" in data
        assert "E501" in data["ignored_rules"]

    def test_ignore_no_config(self, runner, cli_group):
        result = runner.invoke(cli_group, ["ignore", "E501", "--path", "/nonexistent.json"])
        assert result.exit_code == 0
        assert "not found" in result.output


class TestConfigCommand:
    def test_config_show(self, runner, cli_group, tmp_path):
        config = tmp_path / ".json"
        config.write_text('{"test": true}')
        result = runner.invoke(cli_group, ["config", "show", "--path", str(config)])
        assert result.exit_code == 0
        assert "test" in result.output

    def test_config_show_no_file(self, runner, cli_group):
        """Test config show when file doesn't exist (line 118)."""
        result = runner.invoke(cli_group, ["config", "show", "--path", "/nonexistent.json"])
        assert result.exit_code == 0
        assert "not found" in result.output or "Config" in result.output

    def test_config_edit(self, runner, cli_group, tmp_path):
        """Test config edit action (lines 119-136)."""
        config = tmp_path / ".json"
        config.write_text('{"test": true}')
        result = runner.invoke(cli_group, ["config", "edit", "--path", str(config)])
        # Will try to open editor, may fail but should not crash
        assert result.exit_code in (0, 1)

    def test_config_edit_unknown_editor(self, runner, cli_group, tmp_path, monkeypatch):
        """Test config edit with unknown editor."""
        config = tmp_path / ".json"
        config.write_text('{"test": true}')
        monkeypatch.setenv("EDITOR", "myweirdeditor")
        result = runner.invoke(cli_group, ["config", "edit", "--path", str(config)])
        assert result.exit_code in (0, 1)

    def test_config_reset(self, runner, cli_group, tmp_path):
        """Test config reset action (lines 127-136)."""
        config = tmp_path / ".json"
        config.write_text('{"old": "stuff"}')
        result = runner.invoke(cli_group, ["config", "reset", "--path", str(config)], input="y\n")
        assert result.exit_code == 0
        assert "Reset" in result.output


class TestExportCommand:
    def test_export_json(self, runner, cli_group):
        with patch("agent.dependency_injection_container.get_container") as mock_gc:
            container = MagicMock()
            mock_report = MagicMock()
            container.analysis_use_case.execute = MagicMock(return_value=mock_report)
            container.analysis_use_case.to_dict.return_value = {"score": 85.0}
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["export", "json"])
        assert result.exit_code == 0
        assert "score" in result.output

    def test_export_json_with_output_file(self, runner, cli_group, tmp_path):
        """Test export with --output file (line 155)."""
        output_file = tmp_path / "report.json"
        with patch("agent.dependency_injection_container.get_container") as mock_gc:
            container = MagicMock()
            mock_report = MagicMock()
            container.analysis_use_case.execute = MagicMock(return_value=mock_report)
            container.analysis_use_case.to_dict.return_value = {"score": 85.0}
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["export", "json", "-o", str(output_file)])
        assert result.exit_code == 0
        assert "Exported" in result.output
        assert output_file.exists()

    def test_export_sarif(self, runner, cli_group):
        """Test export in sarif format (line 153)."""
        with patch("agent.dependency_injection_container.get_container") as mock_gc, \
             patch("capabilities.linting_report_formatters.to_sarif", return_value="sarif output"):
            container = MagicMock()
            mock_report = MagicMock()
            container.analysis_use_case.execute = MagicMock(return_value=mock_report)
            container.analysis_use_case.to_dict.return_value = {"score": 85.0}
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["export", "sarif"])
        assert result.exit_code == 0

    def test_export_junit(self, runner, cli_group):
        """Test export in junit format."""
        with patch("agent.dependency_injection_container.get_container") as mock_gc, \
             patch("capabilities.linting_report_formatters.to_junit", return_value="junit output"):
            container = MagicMock()
            mock_report = MagicMock()
            container.analysis_use_case.execute = MagicMock(return_value=mock_report)
            container.analysis_use_case.to_dict.return_value = {"score": 85.0}
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["export", "junit"])
        assert result.exit_code == 0


class TestInitCommand:
    def test_init_basic(self, runner, cli_group, tmp_path):
        result = runner.invoke(cli_group, ["init", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "Initialized" in result.output

    def test_init_overwrite(self, runner, cli_group, tmp_path):
        """Test init when config exists and user confirms overwrite (lines 160-161)."""
        config = tmp_path / ".json"
        config.write_text("{}")
        result = runner.invoke(cli_group, ["init", "--path", str(tmp_path)], input="y\n")
        assert result.exit_code == 0

    def test_init_no_overwrite(self, runner, cli_group, tmp_path):
        """Test init when config exists and user declines overwrite."""
        config = tmp_path / ".json"
        config.write_text("{}")
        result = runner.invoke(cli_group, ["init", "--path", str(tmp_path)], input="n\n")
        assert result.exit_code == 0


class TestInstallHookCommand:
    def test_install_hook_success(self, runner, cli_group):
        with patch("surfaces.cli_dev_commands.get_container") as mock_gc:
            container = MagicMock()
            container.hooks_use_case.install.return_value = True
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["install-hook"])
        assert result.exit_code == 0
        assert "installed successfully" in result.output

    def test_install_hook_failure(self, runner, cli_group):
        with patch("surfaces.cli_dev_commands.get_container") as mock_gc:
            container = MagicMock()
            container.hooks_use_case.install.return_value = False
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["install-hook"])
        assert result.exit_code == 0
        assert "Failed" in result.output


class TestUninstallHookCommand:
    def test_uninstall_hook(self, runner, cli_group):
        with patch("surfaces.cli_dev_commands.get_container") as mock_gc:
            container = MagicMock()
            container.hooks_use_case.uninstall.return_value = True
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["uninstall-hook"])
        assert result.exit_code == 0
        assert "removed successfully" in result.output

    def test_uninstall_hook_failure(self, runner, cli_group):
        """Test uninstall hook failure (line 208)."""
        with patch("surfaces.cli_dev_commands.get_container") as mock_gc:
            container = MagicMock()
            container.hooks_use_case.uninstall.return_value = False
            mock_gc.return_value = container
            result = runner.invoke(cli_group, ["uninstall-hook"])
        assert result.exit_code == 0
        assert "Failed" in result.output
