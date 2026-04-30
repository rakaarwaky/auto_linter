"""Additional tests for git_diff_scanner to cover line 95 (empty line handling)."""

from unittest.mock import MagicMock, patch
from pathlib import Path
from infrastructure.git_diff_scanner import get_changed_files


class TestGitDiffScannerEmptyLines:
    """Test empty line handling in diff output (line 95)."""

    def test_diff_output_with_empty_lines(self):
        """Diff output containing empty lines should skip them."""
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                mock = MagicMock()
                mock.returncode = 0
                return mock
            mock = MagicMock()
            # Include empty lines in output
            mock.stdout = "A\tfile1.py\n\nM\tfile2.py\n\n"
            mock.returncode = 0
            return mock

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files(root=Path("/tmp"))
            assert result is not None
            assert "file1.py" in result.added
            assert "file2.py" in result.modified
