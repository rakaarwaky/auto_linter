"""Comprehensive tests for infrastructure/python_bandit_adapter.py — 100% coverage."""

import pytest
from unittest.mock import MagicMock, patch
from infrastructure.python_bandit_adapter import BanditAdapter
import json


class TestBanditAdapter:
    def test_name(self):
        assert BanditAdapter().name() == "bandit"

    def test_apply_fix(self):
        assert BanditAdapter().apply_fix("src/app.py") is False

    def test_scan_success(self):
        adapter = BanditAdapter()
        mock_output = json.dumps({
            "results": [
                {
                    "filename": "src/app.py",
                    "line_number": 10,
                    "test_id": "B101",
                    "issue_text": "assert used",
                    "issue_severity": "HIGH"
                }
            ]
        })
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr=""
            )
            with patch("os.path.abspath", return_value="/test/src"):
                result = adapter.scan("src/")
                assert len(result) == 1
                assert result[0].code == "B101"
                assert result[0].severity.value == "high"

    def test_scan_medium_severity(self):
        adapter = BanditAdapter()
        mock_output = json.dumps({
            "results": [
                {
                    "filename": "src/app.py",
                    "line_number": 10,
                    "test_id": "B102",
                    "issue_text": "issue",
                    "issue_severity": "MEDIUM"
                }
            ]
        })
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr=""
            )
            with patch("os.path.abspath", return_value="/test/src"):
                result = adapter.scan("src/")
                assert len(result) == 1
                assert result[0].severity.value == "medium"

    def test_scan_no_output(self):
        adapter = BanditAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="   ",
                stderr=""
            )
            result = adapter.scan("src/")
            assert result == []

    def test_scan_exception(self):
        adapter = BanditAdapter()
        with patch("subprocess.run", side_effect=Exception("Not found")):
            result = adapter.scan("src/")
            assert result == []

    def test_scan_with_bin_path(self):
        adapter = BanditAdapter(bin_path="/custom/bin")
        mock_output = json.dumps({"results": []})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr=""
            )
            result = adapter.scan("src/")
            assert result == []
            # Verify the command uses the custom bin path
            call_args = mock_run.call_args[0][0]
            assert call_args[0].startswith("/custom/bin")
