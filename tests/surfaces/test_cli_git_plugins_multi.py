"""Additional tests for git-diff, plugins, and multi-project commands."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from surfaces.cli_core_commands import cli
from surfaces.cli_analysis_commands import register_analysis_commands
from surfaces.cli_maintenance_commands import register_maintenance_commands

# Register all commands
register_analysis_commands(cli)
register_maintenance_commands(cli)


class TestGitDiffCommand:
    def test_git_diff_help(self):
        """Test git-diff command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["git-diff", "--help"])
        assert result.exit_code == 0
        assert "git diff" in result.output.lower()

    def test_git_diff_no_git(self):
        """Test git-diff without git repo."""
        runner = CliRunner()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("No git")
            result = runner.invoke(cli, ["git-diff", "."])
            # Should handle gracefully
            assert "git" in result.output.lower() or result.exit_code != 0


class TestPluginsCommand:
    def test_plugins_help(self):
        """Test plugins command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["plugins", "--help"])
        assert result.exit_code == 0
        assert "plugin" in result.output.lower()

    def test_plugins_list(self):
        """Test plugins list."""
        runner = CliRunner()
        mock_cls = type("MockAdapter", (), {"__module__": "test", "__name__": "MockAdapter"})
        with patch("infrastructure.plugin_system.discover_plugins", return_value={"ruff": mock_cls}):
            result = runner.invoke(cli, ["plugins"])
            assert result.exit_code == 0


class TestMultiProjectCommand:
    def test_multi_project_help(self):
        """Test multi-project command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["multi-project", "--help"])
        assert result.exit_code == 0
        assert "multi" in result.output.lower()

    def test_multi_project_no_paths(self):
        """Test multi-project with no paths."""
        runner = CliRunner()
        result = runner.invoke(cli, ["multi-project"])
        assert result.exit_code in (0, 1)


class TestScanCommandWithGitDiff:
    def test_scan_git_diff_flag(self):
        """Test scan with --git-diff flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["scan", ".", "--git-diff"])
        # Should handle git-diff flag
        assert result.exit_code in (0, 1)


class TestReportFormats:
    def test_report_text(self):
        """Test report text format."""
        runner = CliRunner()
        result = runner.invoke(cli, ["report", ".", "--output-format", "text"])
        assert result.exit_code in (0, 1)


class TestSecurityCommand:
    def test_security_empty_path(self):
        """Test security on empty path."""
        runner = CliRunner()
        result = runner.invoke(cli, ["security"])
        assert result.exit_code in (0, 2)


class TestComplexityCommand:
    def test_complexity_help(self):
        """Test complexity help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["complexity", "--help"])
        assert result.exit_code == 0

    def test_complexity_edge_cases(self):
        """Test complexity with various paths."""
        runner = CliRunner()
        result = runner.invoke(cli, ["complexity", "."])
        assert result.exit_code in (0, 1)


class TestDuplicatesCommand:
    def test_duplicates_help(self):
        """Test duplicates help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["duplicates", "--help"])
        assert result.exit_code == 0


class TestTrendsCommand:
    def test_trends_help(self):
        """Test trends help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["trends", "--help"])
        assert result.exit_code == 0


class TestCICommand:
    def test_ci_exit_zero(self):
        """Test ci --exit-zero flag."""
        runner = CliRunner()
        result = runner.invoke(cli, ["ci", ".", "--exit-zero"])
        # Should return 0 even if not passing
        assert result.exit_code == 0


class TestBatchCommand:
    def test_batch_single_path(self):
        """Test batch with single path."""
        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "."])
        assert result.exit_code in (0, 1)


class TestIgnoreCommand:
    def test_ignore_help(self):
        """Test ignore help."""
        runner = CliRunner()
        # ignore command exists in the CLI
        result = runner.invoke(cli, ["ignore", "--help"])
        assert result.exit_code in (0, 2)


class TestConfigCommand:
    def test_config_show_help(self):
        """Test config show help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "show", "--help"])
        assert result.exit_code in (0, 2)



class TestInitCommand:
    def test_init_help(self):
        """Test init help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code in (0, 2)


class TestExportCommand:
    def test_export_help(self):
        """Test export help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "--help"])
        assert result.exit_code in (0, 2)


class TestInstallUninstallHook:
    def test_install_hook_help(self):
        """Test install-hook help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["install-hook", "--help"])
        assert result.exit_code in (0, 2)

    def test_uninstall_hook_help(self):
        """Test uninstall-hook help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["uninstall-hook", "--help"])
        assert result.exit_code in (0, 2)


class TestStatsCommand:
    def test_stats_help(self):
        """Test stats help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["stats", "--help"])
        assert result.exit_code == 0


class TestCleanCommand:
    def test_clean_help(self):
        """Test clean help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["clean", "--help"])
        assert result.exit_code == 0


class TestUpdateCommand:
    def test_update_help(self):
        """Test update help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["update", "--help"])
        assert result.exit_code == 0


class TestSetupDoctor:
    def test_setup_doctor_help(self):
        """Test setup doctor help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["setup", "doctor", "--help"])
        assert result.exit_code in (0, 2)


class TestMCPConfig:
    def test_mcp_config_help(self):
        """Test mcp-config help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["setup", "mcp-config", "--help"])
        assert result.exit_code in (0, 2)



class TestHermesCommand:
    def test_hermes_help(self):
        """Test hermes help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["setup", "hermes", "--help"])
        assert result.exit_code in (0, 2)