"""Additional tests for python_analysis_adapters to cover remaining uncovered lines."""

import json
import pytest
from unittest.mock import MagicMock, patch
from infrastructure.python_analysis_adapters import (
    ComplexityAdapter,
    DuplicateAdapter,
    TrendsAdapter,
    DependencyAdapter,
)
from taxonomy.lint_result_models import Severity


class TestRadonAdapterUncovered:
    """Tests for uncovered lines in ComplexityAdapter (Radon)."""

    def test_scan_radon_command_fails(self):
        """Test RadonAdapter.scan when radon command fails (line 35)."""
        adapter = ComplexityAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("radon not found")
            results = adapter.scan(".")
            assert results == []

    def test_parse_complexity_edge_case_no_issues(self, tmp_path):
        """Test _parse_complexity equivalent - radon returns empty data."""
        adapter = ComplexityAdapter()
        py_file = tmp_path / "simple.py"
        py_file.write_text("x = 1\n")
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout=json.dumps({}),
                stderr="",
                returncode=0
            )
            results = adapter.scan(str(py_file))
            assert results == []

    def test_parse_complexity_edge_case_low_complexity(self, tmp_path):
        """Test when complexity is below threshold (<=10)."""
        adapter = ComplexityAdapter()
        py_file = tmp_path / "simple.py"
        py_file.write_text("x = 1\n")
        
        radon_output = {
            str(py_file): [
                {
                    "name": "simple_func",
                    "lineno": 1,
                    "col_offset": 0,
                    "complexity": 5,
                }
            ]
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout=json.dumps(radon_output),
                stderr="",
                returncode=0
            )
            results = adapter.scan(str(py_file))
            assert results == []  # complexity 5 <= 10, should be filtered


class TestDuplicatesAdapterUncovered:
    """Tests for uncovered lines in DuplicateAdapter."""

    def test_scan_duplicates_command_fails(self):
        """Test DuplicatesAdapter.scan handles exceptions (line 82-83)."""
        adapter = DuplicateAdapter()
        with patch("os.path.abspath", side_effect=Exception("path error")):
            results = adapter.scan(".")
            assert results == []


class TestTrendsAdapterUncovered:
    """Tests for uncovered lines in TrendsAdapter."""

    def test_trends_scan_no_history_file(self, tmp_path):
        """Test TrendsAdapter.scan when history file doesn't exist."""
        adapter = TrendsAdapter(history_file=str(tmp_path / "nonexistent"))
        results = adapter.scan(".")
        assert results == []

    def test_trends_scan_quality_trend_negative(self, tmp_path):
        """Test when quality trend is negative."""
        history_file = tmp_path / ".auto_lint_history"
        history_file.write_text(
            json.dumps({"score": 90}) + "\n" +
            json.dumps({"score": 70}) + "\n"
        )
        
        adapter = TrendsAdapter(history_file=str(history_file))
        results = adapter.scan(".")
        assert len(results) == 1
        assert results[0].code == "TREND001"
        assert "90" in results[0].message
        assert "70" in results[0].message

    def test_trends_scan_quality_trend_positive(self, tmp_path):
        """Test when quality trend is positive (no issues reported)."""
        history_file = tmp_path / ".auto_lint_history"
        history_file.write_text(
            json.dumps({"score": 70}) + "\n" +
            json.dumps({"score": 90}) + "\n"
        )
        
        adapter = TrendsAdapter(history_file=str(history_file))
        results = adapter.scan(".")
        assert results == []

    def test_trends_apply_fix(self, tmp_path):
        """Test TrendsAdapter.apply_fix always returns False."""
        adapter = TrendsAdapter()
        assert adapter.apply_fix(".") is False


class TestDependencyAdapterUncovered:
    """Tests for uncovered lines in DependencyAdapter."""

    def test_dependency_scan_command_fails(self):
        """Test DependencyAdapter.scan when pip-audit fails."""
        adapter = DependencyAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("pip-audit not found")
            results = adapter.scan(".")
            assert results == []
