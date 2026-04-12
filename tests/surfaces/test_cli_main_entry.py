"""Tests for CLI main entry point — command registration."""

import pytest
from click.testing import CliRunner
from surfaces.cli_main_entry import cli


class TestMainEntry:
    """Test that all commands are properly registered on the CLI group."""

    def test_cli_group_exists(self):
        """Verify CLI group is properly configured."""
        assert cli is not None
        assert hasattr(cli, "commands")

    def test_core_commands_registered(self):
        """Verify core commands are registered."""
        expected = ["check", "scan", "fix", "report", "version", "adapters", "security"]
        for cmd in expected:
            assert cmd in cli.commands, f"Command '{cmd}' not registered"

    def test_analysis_commands_registered(self):
        """Verify analysis commands are registered."""
        expected = ["complexity", "duplicates", "trends", "ci", "batch"]
        for cmd in expected:
            assert cmd in cli.commands, f"Command '{cmd}' not registered"

    def test_dev_commands_registered(self):
        """Verify dev commands are registered."""
        expected = ["diff", "suggest", "ignore", "config", "export", "init",
                    "install-hook", "uninstall-hook"]
        for cmd in expected:
            assert cmd in cli.commands, f"Command '{cmd}' not registered"

    def test_maintenance_commands_registered(self):
        """Verify maintenance commands are registered."""
        expected = ["stats", "clean", "update", "doctor"]
        for cmd in expected:
            assert cmd in cli.commands, f"Command '{cmd}' not registered"

    def test_watch_command_registered(self):
        """Verify watch command is registered."""
        assert "watch" in cli.commands, "Command 'watch' not registered"

    def test_setup_group_registered(self):
        """Verify setup group is registered."""
        assert "setup" in cli.commands, "Command 'setup' not registered"

    def test_help_shows_all_commands(self):
        """Verify help output shows all commands."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # Check for key commands in help
        for cmd in ["check", "fix", "report", "version", "doctor", "watch", "setup"]:
            assert cmd in result.output, f"Command '{cmd}' not in help output"

    def test_version_from_entry(self):
        """Test version command works through main entry."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "Auto-Linter" in result.output

    def test_adapters_from_entry(self):
        """Test adapters command works through main entry."""
        runner = CliRunner()
        result = runner.invoke(cli, ["adapters"])
        assert result.exit_code == 0
        assert "ruff" in result.output

    def test_command_count(self):
        """Verify reasonable number of commands are registered."""
        # Should have at least 20 commands
        assert len(cli.commands) >= 20, f"Only {len(cli.commands)} commands registered"
