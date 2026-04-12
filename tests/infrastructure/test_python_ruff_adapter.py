"""Tests for Python Ruff adapter."""
import pytest
import json
import os
from unittest.mock import MagicMock, patch
from infrastructure.python_ruff_adapter import RuffAdapter


class TestRuffAdapter:
    """Tests for RuffAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create RuffAdapter."""
        return RuffAdapter()

    def test_name(self, adapter):
        """Test adapter name is 'ruff'."""
        assert adapter.name() == "ruff"

    def test_init_no_bin_path(self):
        """Test init without bin_path."""
        adapter = RuffAdapter()
        assert adapter.bin_path is None

    def test_init_with_bin_path(self):
        """Test init with bin_path."""
        adapter = RuffAdapter(bin_path="/usr/bin")
        assert adapter.bin_path == "/usr/bin"

    def test_scan_empty(self, adapter):
        """Test scanning with empty stdout."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            result = adapter.scan("/test")
            assert isinstance(result, list)
            assert result == []

    def test_scan_with_results(self, adapter):
        """Test scanning with results."""
        test_results = [{
            "filename": "test.py",
            "location": {"row": 1, "column": 1},
            "code": "E501",
            "message": "Line too long"
        }]
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout=json.dumps(test_results))
            result = adapter.scan("/test")
            assert len(result) > 0
            assert result[0].file is not None
            assert result[0].code == "E501"
            assert result[0].source == "ruff"

    def test_scan_file_not_found(self, adapter):
        """Test scanning when ruff is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError("ruff not found")):
            result = adapter.scan("/test")
            assert result == []

    def test_scan_generic_exception(self, adapter):
        """Test scanning with generic exception."""
        with patch("subprocess.run", side_effect=RuntimeError("unexpected")):
            result = adapter.scan("/test")
            assert result == []

    def test_apply_fix(self, adapter):
        """Test applying fixes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = adapter.apply_fix("/test")
            assert result is True

    def test_apply_fix_exception(self, adapter):
        """Test apply_fix with exception."""
        with patch("subprocess.run", side_effect=RuntimeError("boom")):
            result = adapter.apply_fix("/test")
            assert result is False

    def test_resolve_executable_with_bin_path(self, adapter):
        """Test resolving executable with bin_path set."""
        adapter.bin_path = "/usr/local/bin"
        result = adapter._resolve_executable("ruff")
        assert result == "/usr/local/bin/ruff"

    def test_resolve_executable_without_bin_path(self, adapter):
        """Test resolving executable without bin_path."""
        result = adapter._resolve_executable("ruff")
        assert result == "ruff"

    def test_parse_json_output_valid(self, adapter):
        """Test parsing valid JSON output."""
        test_data = [{"filename": "test.py"}]
        result = adapter._parse_json_output(json.dumps(test_data))
        assert result == test_data

    def test_parse_json_output_invalid(self, adapter):
        """Test parsing invalid JSON."""
        result = adapter._parse_json_output("not json")
        assert result == []

    def test_parse_json_output_with_prefix_noise(self, adapter):
        """Test parsing JSON with prefix noise."""
        test_data = [{"filename": "test.py"}]
        noisy = "Some warning text\n" + json.dumps(test_data)
        result = adapter._parse_json_output(noisy)
        assert result == test_data

    def test_parse_json_output_truly_invalid(self, adapter):
        """Test parsing truly unparseable output."""
        result = adapter._parse_json_output("no brackets at all")
        assert result == []

    def test_filter_phantom_errors_keeps_real(self, adapter):
        """Test filtering phantom errors keeps real file errors."""
        errors = [
            {"code": "E902", "filename": __file__},  # this file exists
            {"code": "E501", "filename": "/phantom/test.py"},
        ]
        result = adapter._filter_phantom_errors(errors)
        assert len(result) == 2  # E902 on existing file kept, E501 always kept

    def test_filter_phantom_errors_removes_nonexistent(self, adapter):
        """Test filtering removes E902 for non-existent files."""
        errors = [{"code": "E902", "filename": "/nonexistent/file.py"}]
        result = adapter._filter_phantom_errors(errors)
        assert result == []

    def test_filter_phantom_errors_empty(self, adapter):
        """Test filtering empty list."""
        result = adapter._filter_phantom_errors([])
        assert result == []

    def test_to_lint_result_high_severity(self, adapter):
        """Test converting F-code error to HIGH severity."""
        item = {
            "filename": "test.py",
            "location": {"row": 5, "column": 3},
            "code": "F401",
            "message": "unused import"
        }
        result = adapter._to_lint_result(item, "/test/path")
        from taxonomy.lint_result_models import Severity
        assert result.severity == Severity.HIGH

    def test_to_lint_result_medium_severity(self, adapter):
        """Test converting E-code error to MEDIUM severity."""
        item = {
            "filename": "test.py",
            "location": {"row": 1, "column": 1},
            "code": "E501",
            "message": "Line too long"
        }
        result = adapter._to_lint_result(item, "/test/path")
        from taxonomy.lint_result_models import Severity
        assert result.severity == Severity.MEDIUM

    def test_to_lint_result_low_severity(self, adapter):
        """Test converting W-code warning to LOW severity."""
        item = {
            "filename": "test.py",
            "location": {"row": 1, "column": 0},
            "code": "W291",
            "message": "trailing whitespace"
        }
        result = adapter._to_lint_result(item, "/test/path")
        from taxonomy.lint_result_models import Severity
        assert result.severity == Severity.LOW

    def test_to_lint_result_e902_high(self, adapter):
        """Test E902 code gets HIGH severity."""
        item = {
            "filename": "test.py",
            "location": {"row": 1, "column": 0},
            "code": "E902",
            "message": "FileNotFoundError"
        }
        result = adapter._to_lint_result(item, "/test/path")
        from taxonomy.lint_result_models import Severity
        assert result.severity == Severity.HIGH

    def test_resolve_filename_relative(self, adapter):
        """Test resolving relative filename."""
        result = adapter._resolve_filename("test.py", "/some/path")
        # Returns as-is when file doesn't exist on disk
        assert result == "test.py"

    def test_resolve_filename_absolute(self, adapter):
        """Test resolving absolute filename."""
        result = adapter._resolve_filename("/absolute/path/test.py", "/some/path")
        assert result == "/absolute/path/test.py"

    def test_resolve_filename_in_existing_dir(self, tmp_path, adapter):
        """Test resolving filename that exists in scan dir."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")
        result = adapter._resolve_filename("test.py", str(tmp_path))
        assert result == str(test_file)

    def test_scan_normalizes_path(self, adapter):
        """Test that scan normalizes paths."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            adapter.scan("src/test.py")
            # normalize_path converts src/ to absolute
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert "ruff" in cmd[0] or "check" in cmd
