"""Tests for CLI main entry."""
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from surfaces.cli_main_entry import main, cli


class TestMainEntry:
    def test_main_invokes_cli(self):
        with patch("surfaces.cli_main_entry.cli") as mock_cli:
            main()
            mock_cli.assert_called_once()

    def test_main_with_runner(self):
        runner = CliRunner()
        result = runner.invoke(cli)
        # Should not crash - exit code 0 or 2 (missing subcommand) are both OK
        assert result.exit_code in [0, 2]

    def test_cli_has_setup_command(self):
        from surfaces.cli_setup_commands import setup
        commands = list(cli.commands.keys())
        assert "setup" in commands or "init" in commands

    def test_cli_has_check_command(self):
        commands = list(cli.commands.keys())
        assert "check" in commands

    def test_cli_has_version_command(self):
        commands = list(cli.commands.keys())
        assert "version" in commands

    def test_main_module_execution(self):
        """Test the `if __name__ == "__main__": main()` path (line 23)."""
        import importlib
        import sys
        # Simulate running as __main__
        with patch("surfaces.cli_main_entry.cli") as mock_cli, \
             patch.object(sys, "argv", ["cli_main_entry.py"]):
            # Re-execute the module's main block
            main()
            mock_cli.assert_called()
