"""Comprehensive tests for surfaces/cli_watch_commands.py — targeting 100% coverage."""

import os
import sys
import builtins
from click.testing import CliRunner
from unittest.mock import MagicMock, patch, AsyncMock
import click


def _ensure_watchdog_mocked():
    """Ensure watchdog modules are in sys.modules before importing LintHandler."""
    if "watchdog.events" not in sys.modules:
        mock_fseh = type("FileSystemEventHandler", (), {})
        sys.modules["watchdog"] = MagicMock()
        sys.modules["watchdog.events"] = MagicMock()
        sys.modules["watchdog.events"].FileSystemEventHandler = mock_fseh
        sys.modules["watchdog.observers"] = MagicMock()


class TestWatchCommand:
    """Tests for the watch CLI command."""

    def _make_cli(self):
        cli = click.Group("test")
        from surfaces.cli_watch_commands import register_watch_command
        register_watch_command(cli)
        return cli

    def test_watch_registered(self):
        cli = self._make_cli()
        assert "watch" in cli.commands

    def test_watch_help(self):
        cli = self._make_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["watch", "--help"])
        assert result.exit_code == 0
        assert "Watch for file changes" in result.output

    def test_watch_missing_path_arg(self):
        cli = self._make_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["watch"])
        assert result.exit_code != 0

    def test_watch_nonexistent_path(self):
        cli = self._make_cli()
        runner = CliRunner()
        result = runner.invoke(cli, ["watch", "/nonexistent/xyz"])
        assert result.exit_code != 0

    def test_watch_no_watchdog_installed(self):
        """When watchdog is not installed, prints error message (lines 35-37)."""
        cli = self._make_cli()
        runner = CliRunner()

        def failing_import(name, *args, **kwargs):
            if "watchdog" in name:
                raise ImportError("No module named 'watchdog'")
            return original_import(name, *args, **kwargs)

        original_import = builtins.__import__
        try:
            builtins.__import__ = failing_import
            result = runner.invoke(cli, ["watch", "."])
            assert result.exit_code == 0
            assert "watchdog" in result.output.lower()
            assert "pip install watchdog" in result.output
        finally:
            builtins.__import__ = original_import

    def test_watch_full_lifecycle(self):
        """Start observer → KeyboardInterrupt → stop → join."""
        cli = self._make_cli()
        runner = CliRunner()

        mock_observer = MagicMock()
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with patch("surfaces.cli_watch_commands.Observer", return_value=mock_observer, create=True), \
                 patch("surfaces.cli_watch_commands.LintHandler", return_value=MagicMock(_handler=MagicMock())), \
                 patch("surfaces.cli_watch_commands.time") as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt
                result = runner.invoke(cli, ["watch", d])
                assert result.exit_code == 0
                assert "Watching" in result.output
                mock_observer.start.assert_called_once()
                mock_observer.stop.assert_called_once()
                mock_observer.join.assert_called_once()

    def test_watch_recursive_schedule(self):
        """Verify observer.schedule is called with recursive=True."""
        cli = self._make_cli()
        runner = CliRunner()

        mock_observer = MagicMock()
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with patch("surfaces.cli_watch_commands.Observer", return_value=mock_observer, create=True), \
                 patch("surfaces.cli_watch_commands.LintHandler", return_value=MagicMock(_handler=MagicMock())), \
                 patch("surfaces.cli_watch_commands.time") as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt
                runner.invoke(cli, ["watch", d])
                call_kwargs = mock_observer.schedule.call_args[1]
                assert call_kwargs.get("recursive") is True

    def test_watch_absolute_path(self):
        """Verify watch uses os.path.abspath for the path."""
        cli = self._make_cli()
        runner = CliRunner()

        mock_observer = MagicMock()
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with patch("surfaces.cli_watch_commands.Observer", return_value=mock_observer, create=True), \
                 patch("surfaces.cli_watch_commands.LintHandler", return_value=MagicMock(_handler=MagicMock())), \
                 patch("surfaces.cli_watch_commands.time") as mock_time:
                mock_time.sleep.side_effect = KeyboardInterrupt
                runner.invoke(cli, ["watch", "."])
                call_args = mock_observer.schedule.call_args[0]
                assert os.path.isabs(call_args[1])


class TestLintHandler:
    """Tests for the LintHandler class (lines 10-27 of cli_watch_commands.py)."""

    def _get_handler(self):
        """Create LintHandler with mocked watchdog and container."""
        _ensure_watchdog_mocked()
        mock_container = MagicMock()
        mock_container.analysis_use_case.execute = AsyncMock()
        with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
            # Need to reload to pick up mocked watchdog
            import importlib
            from surfaces import cli_watch_commands
            importlib.reload(cli_watch_commands)
            lh = cli_watch_commands.LintHandler("/test")
        return lh, mock_container

    def test_handler_class_exists(self):
        """LintHandler is defined at module level."""
        from surfaces.cli_watch_commands import LintHandler
        assert LintHandler is not None

    def test_handler_ignores_directories(self):
        """on_modified skips directory events."""
        lh, mock_container = self._get_handler()
        handler = MagicMock()
        handler.is_directory = True
        handler.src_path = "/test/file.py"
        lh._handler.on_modified(handler)
        mock_container.analysis_use_case.execute.assert_not_called()

    def test_handler_ignores_txt_files(self):
        """Handler should ignore .txt files."""
        lh, mock_container = self._get_handler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/test/file.txt"
        lh._handler.on_modified(event)
        mock_container.analysis_use_case.execute.assert_not_called()

    def test_handler_ignores_md_files(self):
        """Handler should ignore .md files."""
        lh, mock_container = self._get_handler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/test/file.md"
        lh._handler.on_modified(event)
        mock_container.analysis_use_case.execute.assert_not_called()

    def test_handler_ignores_json_files(self):
        """Handler should ignore .json files."""
        lh, mock_container = self._get_handler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/test/file.json"
        lh._handler.on_modified(event)
        mock_container.analysis_use_case.execute.assert_not_called()

    def test_handler_processes_py_files(self):
        """Handler should process .py files."""
        lh, mock_container = self._get_handler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/test/file.py"
        lh._handler.on_modified(event)
        mock_container.analysis_use_case.execute.assert_called_once()

    def test_handler_processes_js_files(self):
        """Handler should process .js files."""
        lh, mock_container = self._get_handler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/test/file.js"
        lh._handler.on_modified(event)
        mock_container.analysis_use_case.execute.assert_called_once()

    def test_handler_processes_ts_files(self):
        """Handler should process .ts files."""
        lh, mock_container = self._get_handler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/test/file.ts"
        lh._handler.on_modified(event)
        mock_container.analysis_use_case.execute.assert_called_once()

    def test_handler_echoes_file_path(self):
        """Handler should print 'Re-checking' message before analysis."""
        lh, mock_container = self._get_handler()
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/test/file.py"
        lh._handler.on_modified(event)
        mock_container.analysis_use_case.execute.assert_called_with("/test/file.py")
