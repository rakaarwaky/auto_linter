"""Additional tests for javascript_linter_adapter to cover line 37."""

from unittest.mock import patch
import subprocess
from infrastructure.javascript_linter_adapter import PrettierAdapter


class TestPrettierAdapterExecutableNotFound:
    """Test when Prettier executable is not found (line 37)."""

    def test_prettier_npx_not_found(self):
        """Test scan when npx/prettier is not found."""
        adapter = PrettierAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("npx not found")
            results = adapter.scan("test.ts")
            assert results == []

    def test_prettier_apply_npx_not_found(self):
        """Test apply_fix when npx/prettier is not found."""
        adapter = PrettierAdapter()
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("npx not found")
            result = adapter.apply_fix("test.ts")
            assert result is False  # apply_fix catches exception and returns False
