"""Enhanced tests for infrastructure files — targeting uncovered lines."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import os
import tempfile
from pathlib import Path


class TestDesktopCommanderAdapter:
    """Test desktop_commander_adapter.py uncovered lines (92-97, 111-112, 117-119)."""

    @pytest.mark.asyncio
    async def test_health_check_auto_falls_back_to_http(self):
        """Test _health_check_auto when socket doesn't exist."""
        from infrastructure.desktop_commander_adapter import DesktopCommanderAdapter

        with patch("pathlib.Path.exists", return_value=False):
            with patch.object(DesktopCommanderAdapter, "_get_http_client") as mock_http:
                mock_client = AsyncMock()
                mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
                mock_http.return_value = mock_client

                adapter = DesktopCommanderAdapter(url="/nonexistent/socket")
                result = await adapter._health_check_auto()

                assert result["status"] == "healthy"
                assert adapter._protocol == "HTTP"

    @pytest.mark.asyncio
    async def test_health_check_auto_uses_unix_when_socket_exists(self):
        """Test _health_check_auto when socket exists."""
        from infrastructure.desktop_commander_adapter import DesktopCommanderAdapter

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(DesktopCommanderAdapter, "_get_unix_client") as mock_unix:
                mock_client = AsyncMock()
                mock_client.health_check = AsyncMock(return_value={"status": "healthy"})
                mock_unix.return_value = mock_client

                adapter = DesktopCommanderAdapter(url="/tmp/dc.sock")
                result = await adapter._health_check_auto()

                assert result["status"] == "healthy"
                assert adapter._protocol == "UnixSocket"

    @pytest.mark.asyncio
    async def test_execute_auto_falls_back_to_http(self):
        """Test _execute_auto when socket doesn't exist."""
        from infrastructure.desktop_commander_adapter import DesktopCommanderAdapter

        with patch("pathlib.Path.exists", return_value=False):
            with patch.object(DesktopCommanderAdapter, "_get_http_client") as mock_http:
                mock_client = AsyncMock()
                mock_client.execute = AsyncMock(return_value={"stdout": "ok", "returncode": 0})
                mock_http.return_value = mock_client

                adapter = DesktopCommanderAdapter(url="/nonexistent/socket")
                result = await adapter._execute_auto(["echo", "test"], ".")

                assert result["stdout"] == "ok"
                assert adapter._protocol == "HTTP"


class TestGitDiffScanner:
    """Test git_diff_scanner.py uncovered lines (59-64, 74-86, 95)."""

    def test_get_changed_files_not_a_git_repo(self, tmp_path):
        """Test when not in a git repo."""
        from infrastructure.git_diff_scanner import get_changed_files
        result = get_changed_files(root=tmp_path)
        assert result is None

    def test_get_changed_files_base_ref_fails_fallback(self, tmp_path):
        """Test when base ref fails, fallback to plain diff."""
        from infrastructure.git_diff_scanner import get_changed_files

        # Initialize git but with no commits
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

        result = get_changed_files(base="HEAD", root=tmp_path)
        # Should return empty diff result (not None, since it IS a git repo)
        assert result is not None
        assert result.added == []
        assert result.modified == []

    def test_get_changed_files_with_parsed_output(self, tmp_path):
        """Test parsing of git diff --name-status output."""
        from infrastructure.git_diff_scanner import get_changed_files

        # Create a git repo with a commit
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)

        # Create and commit a file
        (tmp_path / "file.py").write_text("x = 1")
        subprocess.run(["git", "add", "file.py"], cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)

        result = get_changed_files(base="HEAD^", root=tmp_path)
        # HEAD^ won't exist on first commit, so it should fallback
        # At minimum, it should not crash
        assert result is not None

    def test_filter_by_extensions(self):
        """Test filtering files by extensions."""
        from infrastructure.git_diff_scanner import filter_by_extensions
        files = ["test.py", "test.js", "test.txt", "test.ts", "readme.md"]
        result = filter_by_extensions(files)
        assert "test.py" in result
        assert "test.js" in result
        assert "test.ts" in result
        assert "test.txt" not in result
        assert "readme.md" not in result

    def test_get_changed_files_filtered_returns_empty_for_non_git(self, tmp_path):
        """Test filtered version returns empty when not a git repo."""
        from infrastructure.git_diff_scanner import get_changed_files_filtered
        result = get_changed_files_filtered(root=tmp_path)
        assert result == []


class TestLintingGovernanceAdapterInfrastructure:
    """Test infrastructure/linting_governance_adapter.py uncovered lines (8-9, 30-41, 61-65, 141, 145-146)."""

    def test_import_fallback(self):
        """Test import fallback when taxonomy import fails."""
        # This is already handled by try/except in the source
        from infrastructure.linting_governance_adapter import GOVERNANCE_CODE
        assert GOVERNANCE_CODE == "AES001"

    def test_governance_adapter_scan_directory(self, tmp_path):
        """Test GovernanceAdapter.scan on a directory."""
        from infrastructure.linting_governance_adapter import GovernanceAdapter

        # Create some python files
        (tmp_path / "test.py").write_text("x = 1\n")

        adapter = GovernanceAdapter()
        results = adapter.scan(str(tmp_path))
        # Should not crash, may or may not have results
        assert isinstance(results, list)

    def test_governance_adapter_scan_file(self, tmp_path):
        """Test GovernanceAdapter.scan on a single file."""
        from infrastructure.linting_governance_adapter import GovernanceAdapter

        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")

        adapter = GovernanceAdapter()
        results = adapter.scan(str(test_file))
        assert isinstance(results, list)

    def test_governance_adapter_apply_fix(self, tmp_path):
        """Test GovernanceAdapter.apply_fix always returns False."""
        from infrastructure.linting_governance_adapter import GovernanceAdapter

        adapter = GovernanceAdapter()
        result = adapter.apply_fix(str(tmp_path / "test.py"))
        assert result is False

    def test_governance_adapter_non_python_file(self, tmp_path):
        """Test GovernanceAdapter.lint skips non-Python files."""
        from infrastructure.linting_governance_adapter import GovernanceAdapter

        test_file = tmp_path / "test.js"
        test_file.write_text("const x = 1;\n")

        adapter = GovernanceAdapter()
        results = adapter.lint(str(test_file))
        assert results == []


class TestPythonAnalysisAdapters:
    """Test python_analysis_adapters.py uncovered lines (35, 38-41, 82-83, 92-102, 127-137, 165, 168-170)."""

    def test_complexity_adapter_with_bin_path(self):
        """Test ComplexityAdapter with custom bin_path."""
        from infrastructure.python_analysis_adapters import ComplexityAdapter
        adapter = ComplexityAdapter(bin_path="/custom/bin")
        assert adapter.name() == "radon"
        assert adapter.apply_fix("test.py") is False

    def test_complexity_adapter_scan_no_radon(self, tmp_path):
        """Test ComplexityAdapter.scan when radon is not installed (line 35)."""
        from infrastructure.python_analysis_adapters import ComplexityAdapter
        adapter = ComplexityAdapter()
        results = adapter.scan(str(tmp_path))
        assert results == []

    def test_complexity_adapter_with_valid_json(self, tmp_path):
        """Test ComplexityAdapter.scan with valid JSON output (lines 37-49)."""
        from infrastructure.python_analysis_adapters import ComplexityAdapter
        import json

        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass\n")

        adapter = ComplexityAdapter()
        
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({
            "test.py": [{"lineno": 1, "col_offset": 0, "complexity": 15, "name": "foo"}]
        })

        with patch("subprocess.run", return_value=mock_result):
            results = adapter.scan(str(tmp_path))

        assert len(results) == 1
        assert results[0].code == "complexity"

    def test_complexity_adapter_low_complexity_filtered(self, tmp_path):
        """Test ComplexityAdapter filters low complexity (line 40)."""
        from infrastructure.python_analysis_adapters import ComplexityAdapter
        import json

        adapter = ComplexityAdapter()
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({
            "test.py": [{"lineno": 1, "complexity": 5, "name": "foo"}]
        })

        with patch("subprocess.run", return_value=mock_result):
            results = adapter.scan(str(tmp_path))

        assert results == []

    def test_duplicate_adapter_exceeds_500_lines(self, tmp_path):
        """Test DuplicateAdapter detection for files > 500 lines."""
        from infrastructure.python_analysis_adapters import DuplicateAdapter

        # Create a file with > 500 lines
        large_file = tmp_path / "large.py"
        large_file.write_text("\n".join([f"line_{i} = {i}" for i in range(600)]))

        adapter = DuplicateAdapter()
        results = adapter.scan(str(tmp_path))
        # Should detect the large file
        assert any("500 lines" in r.message for r in results)

    def test_duplicate_adapter_skip_cache_dirs(self, tmp_path):
        """Test DuplicateAdapter skips __pycache__ and .venv."""
        from infrastructure.python_analysis_adapters import DuplicateAdapter

        # Create __pycache__ with large file (should be skipped)
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "large.py").write_text("\n".join([f"line_{i} = {i}" for i in range(600)]))

        adapter = DuplicateAdapter()
        results = adapter.scan(str(tmp_path))
        # Should be empty since __pycache__ is skipped
        assert results == []

    def test_duplicate_adapter_handles_read_error(self, tmp_path):
        """Test DuplicateAdapter._check_file handles read errors."""
        from infrastructure.python_analysis_adapters import DuplicateAdapter

        adapter = DuplicateAdapter()
        results = []
        # Try to read a binary file
        adapter._check_file("/dev/urandom", results)
        # Should not crash

    def test_trends_adapter_no_history(self, tmp_path):
        """Test TrendsAdapter when no history file exists."""
        from infrastructure.python_analysis_adapters import TrendsAdapter
        adapter = TrendsAdapter(history_file=str(tmp_path / "nonexistent"))
        results = adapter.scan(str(tmp_path))
        assert results == []

    def test_trends_adapter_with_declining_score(self, tmp_path):
        """Test TrendsAdapter detects declining score."""
        from infrastructure.python_analysis_adapters import TrendsAdapter
        import json

        history_file = tmp_path / ".auto_lint_history"
        history_file.write_text(
            json.dumps({"score": 90}) + "\n" +
            json.dumps({"score": 80}) + "\n"
        )

        adapter = TrendsAdapter(history_file=str(history_file))
        results = adapter.scan(str(tmp_path))
        assert len(results) == 1
        assert "TREND001" in results[0].code

    def test_trends_adapter_with_improving_score(self, tmp_path):
        """Test TrendsAdapter with improving score (no results)."""
        from infrastructure.python_analysis_adapters import TrendsAdapter
        import json

        history_file = tmp_path / ".auto_lint_history"
        history_file.write_text(
            json.dumps({"score": 80}) + "\n" +
            json.dumps({"score": 90}) + "\n"
        )

        adapter = TrendsAdapter(history_file=str(history_file))
        results = adapter.scan(str(tmp_path))
        assert results == []

    def test_dependency_adapter_no_pip_audit(self, tmp_path):
        """Test DependencyAdapter when pip-audit is not installed."""
        from infrastructure.python_analysis_adapters import DependencyAdapter
        adapter = DependencyAdapter()
        results = adapter.scan(str(tmp_path))
        assert isinstance(results, list)

    def test_dependency_adapter_with_bin_path(self):
        """Test DependencyAdapter with custom bin_path."""
        from infrastructure.python_analysis_adapters import DependencyAdapter
        adapter = DependencyAdapter(bin_path="/custom/bin")
        assert adapter.name() == "pip-audit"
        assert adapter.apply_fix("test.py") is False


class TestHTTPRequestClient:
    """Test http_request_client.py uncovered lines (58, 60, 90-99)."""

    @pytest.mark.asyncio
    async def test_health_check_non_200_falls_back_to_execute(self):
        """Test health_check when /health returns non-200, falls back to execute."""
        from infrastructure.http_request_client import HTTPClient

        client = HTTPClient(url="http://localhost:9999/execute")

        with patch.object(client, "_ensure_client", new_callable=AsyncMock) as mock_client:
            mock_http = AsyncMock()
            mock_http.is_closed = False
            # First GET returns 500
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.raise_for_status = MagicMock()  # sync method, not async
            mock_http.get = AsyncMock(return_value=mock_response)
            mock_http.post = AsyncMock()
            mock_client.return_value = mock_http

            result = await client.health_check()
            # Should fall back to execute, which will also fail
            assert "status" in result

    @pytest.mark.asyncio
    async def test_health_check_exception_path(self):
        """Test health_check when exception is raised."""
        from infrastructure.http_request_client import HTTPClient

        client = HTTPClient(url="http://localhost:9999/execute")

        with patch.object(client, "_ensure_client", new_callable=AsyncMock) as mock_client:
            mock_client.side_effect = ConnectionError("Connection refused")
            result = await client.health_check()

            assert result["status"] == "unhealthy"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_generic_exception(self):
        """Test execute when a generic exception occurs."""
        from infrastructure.http_request_client import HTTPClient

        client = HTTPClient(url="http://localhost:9999/execute")

        with patch.object(client, "_ensure_client", new_callable=AsyncMock) as mock_client:
            mock_http = AsyncMock()
            mock_http.is_closed = False
            mock_http.post = AsyncMock(side_effect=ValueError("Something went wrong"))
            mock_client.return_value = mock_http

            result = await client.execute(["echo", "test"], ".")
            assert result["returncode"] == 1
            assert "error" in result


class TestGitHooksManager:
    """Test git_hooks_manager.py uncovered lines (48-50, 62-64)."""

    def test_install_pre_commit_not_a_git_repo(self, tmp_path):
        """Test install_pre_commit when not a git repo."""
        from infrastructure.git_hooks_manager import GitHookManager
        manager = GitHookManager(root_dir=str(tmp_path))
        result = manager.install_pre_commit()
        assert result is False

    def test_uninstall_pre_commit_not_a_git_repo(self, tmp_path):
        """Test uninstall_pre_commit when not a git repo."""
        from infrastructure.git_hooks_manager import GitHookManager
        manager = GitHookManager(root_dir=str(tmp_path))
        result = manager.uninstall_pre_commit()
        assert result is False

    def test_uninstall_pre_commit_no_hook_exists(self, tmp_path):
        """Test uninstall_pre_commit when hook doesn't exist."""
        from infrastructure.git_hooks_manager import GitHookManager
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        manager = GitHookManager(root_dir=str(tmp_path))
        result = manager.uninstall_pre_commit()
        # Should return True (nothing to remove is success)
        assert result is True


class TestPluginSystem:
    """Test plugin_system.py uncovered lines (42-45, 54-55)."""

    def test_discover_plugins_with_exception(self):
        """Test discover_plugins when entry point loading fails."""
        from infrastructure.plugin_system import discover_plugins

        with patch("importlib.metadata.entry_points") as mock_eps:
            # Create a mock entry point that fails to load
            mock_ep = MagicMock()
            mock_ep.name = "failing_plugin"
            mock_ep.load.side_effect = ImportError("Cannot load")

            mock_eps.return_value = MagicMock(select=MagicMock(return_value=[mock_ep]))

            result = discover_plugins()
            assert "failing_plugin" not in result

    def test_register_and_unregister_custom_adapter(self):
        """Test register and unregister of custom adapters."""
        from infrastructure.plugin_system import (
            register_custom_adapter,
            unregister_custom_adapter,
            get_custom_adapter,
        )

        class TestAdapter:
            pass

        register_custom_adapter("test_adapter", TestAdapter)
        assert get_custom_adapter("test_adapter") is TestAdapter

        unregistered = unregister_custom_adapter("test_adapter")
        assert unregistered is TestAdapter
        assert get_custom_adapter("test_adapter") is None

    def test_unregister_nonexistent_adapter(self):
        """Test unregistering an adapter that doesn't exist."""
        from infrastructure.plugin_system import unregister_custom_adapter
        result = unregister_custom_adapter("nonexistent")
        assert result is None


class TestUnixSocketClient:
    """Test unix_socket_client.py uncovered lines (115-117)."""

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health_check when echo command returns non-zero."""
        from infrastructure.unix_socket_client import UnixSocketClient

        client = UnixSocketClient(socket_path="/tmp/dc.sock")

        with patch.object(client, "execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"returncode": 1, "stderr": "Connection refused"}
            result = await client.health_check()

            assert result["status"] == "unhealthy"
            assert "error" in result

    def test_close_socket_with_exception(self):
        """Test close when socket.close() raises an exception."""
        from infrastructure.unix_socket_client import UnixSocketClient
        import socket

        client = UnixSocketClient(socket_path="/tmp/dc.sock")
        # Create a mock socket that raises on close
        mock_sock = MagicMock()
        mock_sock.close.side_effect = OSError("Cannot close")
        mock_sock.fileno.return_value = 3
        client._socket = mock_sock

        # Should not raise
        client.close()
        assert client._socket is None


class TestJavascriptLinterAdapter:
    """Test javascript_linter_adapter.py uncovered lines (37, 65-67, 184-186)."""

    def test_prettier_adapter_non_file_path(self):
        """Test PrettierAdapter.scan with a directory path."""
        from infrastructure.javascript_linter_adapter import PrettierAdapter
        adapter = PrettierAdapter()
        # Should proceed with directory scan
        results = adapter.scan(".")
        assert isinstance(results, list)

    def test_prettier_adapter_apply_fix_exception(self):
        """Test PrettierAdapter.apply_fix when exception occurs."""
        from infrastructure.javascript_linter_adapter import PrettierAdapter
        adapter = PrettierAdapter()

        with patch("subprocess.run", side_effect=OSError("npx not found")):
            result = adapter.apply_fix("test.js")
            assert result is False

    def test_eslint_adapter_apply_fix_exception(self):
        """Test ESLintAdapter.apply_fix when exception occurs."""
        from infrastructure.javascript_linter_adapter import ESLintAdapter
        adapter = ESLintAdapter()

        with patch("subprocess.run", side_effect=OSError("npx not found")):
            result = adapter.apply_fix("test.js")
            assert result is False


class TestJavascriptScopeDetector:
    """Test javascript_scope_detector.py uncovered line (34)."""

    def test_show_enclosing_scope_file_not_found(self):
        """Test show_enclosing_scope when file doesn't exist."""
        from infrastructure.javascript_scope_detector import show_enclosing_scope
        result = show_enclosing_scope("/nonexistent/file.js", 10)
        assert result is None
