"""Tests for cli_watch_commands.py - targeting 100% coverage."""

import sys
from unittest.mock import MagicMock, patch, AsyncMock
import click
from click.testing import CliRunner


def test_lint_handler_init():
    """Test LintHandler initialization (lines 10-25)."""
    # Mock watchdog module before importing
    mock_fseh = type("FileSystemEventHandler", (), {})
    sys.modules["watchdog"] = MagicMock()
    sys.modules["watchdog.events"] = MagicMock()
    sys.modules["watchdog.events"].FileSystemEventHandler = mock_fseh
    sys.modules["watchdog.observers"] = MagicMock()
    
    from surfaces.cli_watch_commands import LintHandler
    
    mock_container = MagicMock()
    with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
        handler = LintHandler("/test/path")
        assert handler._handler is not None
        assert hasattr(handler._handler, "_path")
        assert hasattr(handler._handler, "_container")


def test_lint_handler_on_modified_directory():
    """Test LintHandler ignores directory events (lines 19-20)."""
    mock_fseh = type("FileSystemEventHandler", (), {})
    sys.modules["watchdog"] = MagicMock()
    sys.modules["watchdog.events"] = MagicMock()
    sys.modules["watchdog.events"].FileSystemEventHandler = mock_fseh
    
    from surfaces.cli_watch_commands import LintHandler
    
    mock_container = MagicMock()
    with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
        handler = LintHandler("/test")
        event = MagicMock()
        event.is_directory = True
        event.src_path = "/test/file.py"
        handler._handler.on_modified(event)
        mock_container.analysis_use_case.execute.assert_not_called()


def test_lint_handler_on_modified_non_code_file():
    """Test LintHandler ignores non-code files (lines 19-20)."""
    mock_fseh = type("FileSystemEventHandler", (), {})
    sys.modules["watchdog"] = MagicMock()
    sys.modules["watchdog.events"] = MagicMock()
    sys.modules["watchdog.events"].FileSystemEventHandler = mock_fseh
    
    from surfaces.cli_watch_commands import LintHandler
    
    mock_container = MagicMock()
    with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
        handler = LintHandler("/test")
        event = MagicMock()
        event.is_directory = False
        event.src_path = "/test/file.txt"
        handler._handler.on_modified(event)
        mock_container.analysis_use_case.execute.assert_not_called()


def test_lint_handler_on_modified_py_file():
    """Test LintHandler processes .py files (lines 21-23)."""
    mock_fseh = type("FileSystemEventHandler", (), {})
    sys.modules["watchdog"] = MagicMock()
    sys.modules["watchdog.events"] = MagicMock()
    sys.modules["watchdog.events"].FileSystemEventHandler = mock_fseh
    
    from surfaces.cli_watch_commands import LintHandler
    
    mock_container = MagicMock()
    with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
        with patch("asyncio.run") as mock_run:
            handler = LintHandler("/test")
            event = MagicMock()
            event.is_directory = False
            event.src_path = "/test/file.py"
            handler._handler.on_modified(event)
            mock_run.assert_called_once()


def test_lint_handler_on_modified_js_file():
    """Test LintHandler processes .js files (lines 21-23)."""
    mock_fseh = type("FileSystemEventHandler", (), {})
    sys.modules["watchdog"] = MagicMock()
    sys.modules["watchdog.events"] = MagicMock()
    sys.modules["watchdog.events"].FileSystemEventHandler = mock_fseh
    
    from surfaces.cli_watch_commands import LintHandler
    
    mock_container = MagicMock()
    with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
        with patch("asyncio.run") as mock_run:
            handler = LintHandler("/test")
            event = MagicMock()
            event.is_directory = False
            event.src_path = "/test/file.js"
            handler._handler.on_modified(event)
            mock_run.assert_called_once()


def test_lint_handler_on_modified_ts_file():
    """Test LintHandler processes .ts files (lines 21-23)."""
    mock_fseh = type("FileSystemEventHandler", (), {})
    sys.modules["watchdog"] = MagicMock()
    sys.modules["watchdog.events"] = MagicMock()
    sys.modules["watchdog.events"].FileSystemEventHandler = mock_fseh
    
    from surfaces.cli_watch_commands import LintHandler
    
    mock_container = MagicMock()
    with patch("agent.dependency_injection_container.get_container", return_value=mock_container):
        with patch("asyncio.run") as mock_run:
            handler = LintHandler("/test")
            event = MagicMock()
            event.is_directory = False
            event.src_path = "/test/file.ts"
            handler._handler.on_modified(event)
            mock_run.assert_called_once()


def test_watch_command_no_watchdog():
    """Test watch command when watchdog is not installed (lines 33-37)."""
    # Remove watchdog from sys.modules
    watchdog_modules = {k: v for k, v in sys.modules.items() if "watchdog" in k}
    for k in watchdog_modules:
        del sys.modules[k]
    
    from surfaces.cli_watch_commands import register_watch_command
    
    @click.group()
    def cli():
        pass
    
    register_watch_command(cli)
    runner = CliRunner()
    
    # Patch import to fail for watchdog
    import builtins
    real_import = builtins.__import__
    def mock_import(name, *args, **kwargs):
        if "watchdog" in name:
            raise ImportError("No module named 'watchdog'")
        return real_import(name, *args, **kwargs)
    
    builtins.__import__ = mock_import
    try:
        result = runner.invoke(cli, ["watch", "."])
        assert result.exit_code == 0
        assert "watchdog" in result.output.lower()
    finally:
        builtins.__import__ = real_import
        # Restore watchdog modules
        sys.modules.update(watchdog_modules)


def test_watch_command_success():
    """Test watch command success path (lines 38-50)."""
    # Mock watchdog module
    mock_observer = MagicMock()
    mock_observer_class = MagicMock(return_value=mock_observer)
    mock_fseh = type("FileSystemEventHandler", (), {})
    
    sys.modules["watchdog"] = MagicMock()
    sys.modules["watchdog.events"] = MagicMock()
    sys.modules["watchdog.events"].FileSystemEventHandler = mock_fseh
    sys.modules["watchdog.observers"] = MagicMock()
    sys.modules["watchdog.observers"].Observer = mock_observer_class
    
    from surfaces.cli_watch_commands import register_watch_command
    
    @click.group()
    def cli():
        pass
    
    register_watch_command(cli)
    runner = CliRunner()
    
    with patch("time.sleep", side_effect=KeyboardInterrupt):
        result = runner.invoke(cli, ["watch", "."])
        assert result.exit_code == 0
        assert "Watching" in result.output
        mock_observer.start.assert_called_once()
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()


def test_watch_command_recursive_schedule():
    """Test watch command schedules with recursive=True (line 44)."""
    mock_observer = MagicMock()
    mock_observer_class = MagicMock(return_value=mock_observer)
    mock_fseh = type("FileSystemEventHandler", (), {})
    
    sys.modules["watchdog"] = MagicMock()
    sys.modules["watchdog.events"] = MagicMock()
    sys.modules["watchdog.events"].FileSystemEventHandler = mock_fseh
    sys.modules["watchdog.observers"] = MagicMock()
    sys.modules["watchdog.observers"].Observer = mock_observer_class
    
    from surfaces.cli_watch_commands import register_watch_command
    
    @click.group()
    def cli():
        pass
    
    register_watch_command(cli)
    runner = CliRunner()
    
    with patch("time.sleep", side_effect=KeyboardInterrupt):
        runner.invoke(cli, ["watch", "."])
        call_kwargs = mock_observer.schedule.call_args[1]
        assert call_kwargs.get("recursive") is True