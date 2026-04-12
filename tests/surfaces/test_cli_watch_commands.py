"""Tests for CLI watch commands."""
import pytest
from click.testing import CliRunner
import click


@pytest.fixture
def runner():
    return CliRunner()


class TestWatchCommand:
    def test_watch_watchdog_not_installed(self, runner):
        # Create a CLI group and register watch command
        from surfaces import cli_watch_commands

        @click.group()
        def cli():
            pass

        # Mock the import inside the function
        import sys
        # Remove watchdog from sys.modules if present
        watchdog_modules = [k for k in sys.modules if "watchdog" in k]
        saved = {}
        for mod in watchdog_modules:
            saved[mod] = sys.modules.pop(mod)

        # Patch import to fail on watchdog
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if "watchdog" in name:
                raise ImportError(f"No module named '{name}'")
            return real_import(name, *args, **kwargs)

        builtins.__import__ = mock_import
        try:
            # Reload the module to pick up the mocked import
            if "surfaces.cli_watch_commands" in sys.modules:
                del sys.modules["surfaces.cli_watch_commands"]

            from surfaces.cli_watch_commands import register_watch_command
            register_watch_command(cli)

            result = runner.invoke(cli, ["watch", "."])
            assert result.exit_code == 0
            assert "watchdog" in result.output.lower() or "not installed" in result.output
        finally:
            builtins.__import__ = real_import
            for mod, val in saved.items():
                sys.modules[mod] = val
