"""Tests for Python MyPy adapter."""
import pytest
from unittest.mock import MagicMock, patch
from infrastructure.python_mypy_adapter import MyPyAdapter
from taxonomy.lint_result_models import Severity


class TestMyPyAdapter:
    """Tests for MyPyAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create MyPyAdapter."""
        return MyPyAdapter()

    def test_name(self, adapter):
        """Test adapter name is 'mypy'."""
        assert adapter.name() == "mypy"

    def test_init_no_bin_path(self):
        """Test init without bin_path."""
        adapter = MyPyAdapter()
        assert adapter.bin_path is None

    def test_init_with_bin_path(self):
        """Test init with bin_path."""
        adapter = MyPyAdapter(bin_path="/usr/bin")
        assert adapter.bin_path == "/usr/bin"

    def test_scan_empty(self, adapter):
        """Test scanning with no errors."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = adapter.scan("/test")
            assert isinstance(result, list)
            assert result == []

    def test_scan_with_errors(self, adapter):
        """Test scanning with type errors."""
        stderr = "test.py:1:5: error: Missing type annotation\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr=stderr)
            result = adapter.scan("/test")
            assert len(result) == 1
            assert result[0].code == "mypy"
            assert result[0].message == "Missing type annotation"
            assert result[0].line == 1
            assert result[0].column == 5

    def test_scan_with_warning(self, adapter):
        """Test scanning with warning type."""
        stderr = "test.py:3: warning: Unused import\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr=stderr)
            result = adapter.scan("/test")
            assert len(result) == 1
            assert result[0].severity == Severity.MEDIUM

    def test_scan_with_note(self, adapter):
        """Test scanning with note type."""
        stderr = "test.py:2: note: Some note\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr=stderr)
            result = adapter.scan("/test")
            assert len(result) == 1
            assert result[0].severity == Severity.INFO

    def test_scan_without_column(self, adapter):
        """Test scanning when column number is missing."""
        stderr = "test.py:1: error: Missing type\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr=stderr)
            result = adapter.scan("/test")
            assert len(result) == 1
            assert result[0].column == 0

    def test_scan_file_not_found(self, adapter):
        """Test scanning when mypy is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError("mypy not found")):
            result = adapter.scan("/test")
            assert result == []

    def test_scan_generic_exception(self, adapter):
        """Test scanning with generic exception."""
        with patch("subprocess.run", side_effect=RuntimeError("unexpected")):
            result = adapter.scan("/test")
            assert result == []

    def test_scan_mixed_output(self, adapter):
        """Test scanning with stdout and stderr combined."""
        stdout = "Success: no issues found\n"
        stderr = "test.py:5:10: error: Incompatible types\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout=stdout, stderr=stderr)
            result = adapter.scan("/test")
            assert len(result) == 1
            assert "Incompatible types" in result[0].message

    def test_scan_invalid_lines_ignored(self, adapter):
        """Test that non-matching lines are ignored."""
        stderr = "Some random warning\nNot a mypy output\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr=stderr)
            result = adapter.scan("/test")
            assert result == []

    def test_apply_fix(self, adapter):
        """Test apply_fix always returns False (MyPy doesn't fix)."""
        result = adapter.apply_fix("/test")
        assert result is False

    def test_resolve_executable_with_bin_path(self, adapter):
        """Test resolving executable with bin_path set."""
        adapter.bin_path = "/usr/local/bin"
        result = adapter._resolve_executable("mypy")
        assert result == "/usr/local/bin/mypy"

    def test_resolve_executable_without_bin_path(self, adapter):
        """Test resolving executable without bin_path."""
        result = adapter._resolve_executable("mypy")
        assert result == "mypy"

    def test_map_severity_error(self, adapter):
        """Test mapping error severity."""
        result = adapter._map_severity("error")
        assert result == Severity.HIGH

    def test_map_severity_warning(self, adapter):
        """Test mapping warning severity."""
        result = adapter._map_severity("warning")
        assert result == Severity.MEDIUM

    def test_map_severity_note(self, adapter):
        """Test mapping note severity."""
        result = adapter._map_severity("note")
        assert result == Severity.INFO

    def test_map_severity_unknown(self, adapter):
        """Test mapping unknown severity defaults to HIGH."""
        result = adapter._map_severity("unknown")
        assert result == Severity.HIGH
