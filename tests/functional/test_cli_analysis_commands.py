"""Comprehensive tests for surfaces/cli_analysis_commands.py — 100% coverage."""

import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, AsyncMock, patch
from surfaces.cli_analysis_commands import register_analysis_commands
from surfaces.cli_core_commands import cli
import os


# Register analysis commands
register_analysis_commands(cli)


@pytest.fixture(autouse=True)
def mock_container():
    """Mock the container for all tests."""
    mock = MagicMock()
    mock_report = MagicMock()
    mock_report.results = []
    mock_report.score = 100.0
    mock_report.is_passing = True

    mock.analysis_use_case.execute = AsyncMock(return_value=mock_report)
    mock.analysis_use_case.to_dict = MagicMock(return_value={
        "score": 100.0, "is_passing": True, "radon": [],
        "duplicates": [], "trends": [], "summary": {},
    })
    with patch("surfaces.cli_analysis_commands.get_container", return_value=mock):
        yield mock


@pytest.fixture
def fixtures_path():
    return os.path.dirname(__file__)


class TestComplexityCommand:
    def test_clean(self, fixtures_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["complexity", fixtures_path])
        assert result.exit_code == 0
        assert "within healthy limits" in result.output

    def test_found(self, fixtures_path, mock_container):
        mock_container.analysis_use_case.to_dict.return_value = {
            "score": 80.0, "is_passing": True, "radon": [
                {"file": "src/app.py", "line": 10, "message": "High complexity (15)"}
            ], "summary": {},
        }
        runner = CliRunner()
        result = runner.invoke(cli, ["complexity", fixtures_path])
        assert result.exit_code == 0
        assert "high complexity" in result.output


class TestDuplicatesCommand:
    def test_clean(self, fixtures_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["duplicates", fixtures_path])
        assert result.exit_code == 0
        assert "No major duplication" in result.output

    def test_found(self, fixtures_path, mock_container):
        mock_container.analysis_use_case.to_dict.return_value = {
            "score": 90.0, "is_passing": True, "duplicates": [
                {"file": "src/app.py", "line": 1, "message": "Oversized file"}
            ], "summary": {},
        }
        runner = CliRunner()
        result = runner.invoke(cli, ["duplicates", fixtures_path])
        assert result.exit_code == 0
        assert "Oversized file" in result.output


class TestTrendsCommand:
    def test_stable(self, fixtures_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["trends", fixtures_path])
        assert result.exit_code == 0
        assert "STABLE or IMPROVING" in result.output

    def test_declining(self, fixtures_path, mock_container):
        mock_container.analysis_use_case.to_dict.return_value = {
            "score": 80.0, "is_passing": True, "trends": [
                {"message": "Quality trend is negative: 90 -> 80"}
            ], "summary": {},
        }
        runner = CliRunner()
        result = runner.invoke(cli, ["trends", fixtures_path])
        assert result.exit_code == 0
        assert "negative" in result.output


class TestCICommand:
    def test_passing(self, fixtures_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["ci", fixtures_path])
        assert result.exit_code == 0
        assert "passing=True" in result.output

    def test_failing_no_exit_zero(self, fixtures_path, mock_container):
        mock_report = MagicMock()
        mock_report.score = 50.0
        mock_report.is_passing = False
        mock_container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
        mock_container.analysis_use_case.to_dict.return_value = {
            "score": 50.0, "is_passing": False, "summary": {},
        }
        runner = CliRunner()
        result = runner.invoke(cli, ["ci", fixtures_path])
        assert result.exit_code == 1

    def test_failing_with_exit_zero(self, fixtures_path, mock_container):
        mock_report = MagicMock()
        mock_report.score = 50.0
        mock_report.is_passing = False
        mock_container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
        mock_container.analysis_use_case.to_dict.return_value = {
            "score": 50.0, "is_passing": False, "summary": {},
        }
        runner = CliRunner()
        result = runner.invoke(cli, ["ci", fixtures_path, "--exit-zero"])
        assert result.exit_code == 0


class TestBatchCommand:
    def test_no_paths(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["batch"])
        assert result.exit_code == 0
        assert "No paths" in result.output

    def test_passing(self, fixtures_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["batch", fixtures_path])
        assert result.exit_code == 0
        assert "PASSED" in result.output

    def test_failing(self, fixtures_path, mock_container):
        mock_report = MagicMock()
        mock_report.score = 50.0
        mock_report.is_passing = False
        mock_container.analysis_use_case.execute = AsyncMock(return_value=mock_report)
        mock_container.analysis_use_case.to_dict.return_value = {
            "score": 50.0, "is_passing": False, "summary": {},
        }
        runner = CliRunner()
        result = runner.invoke(cli, ["batch", fixtures_path])
        assert result.exit_code == 1
        assert "FAILED" in result.output
