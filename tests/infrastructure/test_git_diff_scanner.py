"""Tests for git_diff_scanner module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
from infrastructure.git_diff_scanner import (
    DiffResult,
    get_changed_files,
    filter_by_extensions,
    get_changed_files_filtered,
)


class TestDiffResult:
    def test_all_files_empty(self):
        dr = DiffResult(added=[], modified=[], deleted=[], renamed=[])
        assert dr.all_files == []

    def test_all_files_combined(self):
        dr = DiffResult(
            added=["a.py"],
            modified=["b.py"],
            deleted=[],
            renamed=[("old.py", "new.py")],
        )
        assert set(dr.all_files) == {"a.py", "b.py", "new.py"}


class TestGetChangedFiles:
    def test_not_a_git_repo(self):
        """Returns None when not in a git repo."""
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            result = get_changed_files(root=Path("/tmp"))
            assert result is None

    def test_git_not_installed(self):
        """Returns None when git is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = get_changed_files(root=Path("/tmp"))
            assert result is None

    def test_no_changes(self):
        """Returns empty DiffResult when no changes."""
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # git rev-parse succeeds
                mock = MagicMock()
                mock.returncode = 0
                return mock
            # git diff returns no output
            mock = MagicMock()
            mock.stdout = ""
            mock.returncode = 0
            return mock

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files(root=Path("/tmp"))
            assert result is not None
            assert result.added == []
            assert result.modified == []

    def test_added_files(self):
        """Parses added files correctly."""
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                mock = MagicMock()
                mock.returncode = 0
                return mock
            mock = MagicMock()
            mock.stdout = "A\tsrc/new.py\nA\ttests/test_new.py"
            mock.returncode = 0
            return mock

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files(root=Path("/tmp"))
            assert "src/new.py" in result.added
            assert "tests/test_new.py" in result.added

    def test_modified_files(self):
        """Parses modified files correctly."""
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                mock = MagicMock()
                mock.returncode = 0
                return mock
            mock = MagicMock()
            mock.stdout = "M\tsrc/app.py\nM\tsrc/utils.py"
            mock.returncode = 0
            return mock

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files(root=Path("/tmp"))
            assert "src/app.py" in result.modified
            assert "src/utils.py" in result.modified

    def test_deleted_files(self):
        """Parses deleted files correctly."""
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                mock = MagicMock()
                mock.returncode = 0
                return mock
            mock = MagicMock()
            mock.stdout = "D\tsrc/old.py"
            mock.returncode = 0
            return mock

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files(root=Path("/tmp"))
            assert "src/old.py" in result.deleted

    def test_renamed_files(self):
        """Parses renamed files correctly."""
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                mock = MagicMock()
                mock.returncode = 0
                return mock
            mock = MagicMock()
            mock.stdout = "R100\tsrc/old.py\tsrc/new.py"
            mock.returncode = 0
            return mock

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files(root=Path("/tmp"))
            assert ("src/old.py", "src/new.py") in result.renamed

    def test_target_staged(self):
        """Test with target='staged' (lines 59-61)."""
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                mock = MagicMock()
                mock.returncode = 0
                return mock
            # Should use --cached for staged
            cmd = args[0]
            assert "--cached" in cmd, f"Expected --cached in {cmd}"
            mock = MagicMock()
            mock.stdout = ""
            mock.returncode = 0
            return mock

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files(root=Path("/tmp"), target="staged")
            assert result is not None

    def test_target_two_refs(self):
        """Test with target as a ref (lines 62-64)."""
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                mock = MagicMock()
                mock.returncode = 0
                return mock
            # Should have base and target
            cmd = args[0]
            assert "main" in cmd and "develop" in cmd, f"Expected refs in {cmd}"
            mock = MagicMock()
            mock.stdout = ""
            mock.returncode = 0
            return mock

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files(root=Path("/tmp"), base="main", target="develop")
            assert result is not None

    def test_diff_fallback_fails_again(self):
        """Test when both diff commands fail (lines 85-86)."""
        call_count = [0]

        def mock_run(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call (git rev-parse) succeeds
                mock = MagicMock()
                mock.returncode = 0
                return mock
            # Both diff commands fail
            raise subprocess.CalledProcessError(1, "git diff")

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files(root=Path("/tmp"))
            # Should return empty DiffResult
            assert result is not None
            assert result.added == []
            assert result.modified == []


class TestFilterByExtensions:
    def test_filters_python_files(self):
        files = ["a.py", "b.js", "c.txt", "d.ts"]
        result = filter_by_extensions(files)
        assert "a.py" in result
        assert "b.js" in result
        assert "d.ts" in result
        assert "c.txt" not in result

    def test_filters_js_files(self):
        files = ["a.jsx", "b.tsx", "c.md"]
        result = filter_by_extensions(files, (".jsx", ".tsx"))
        assert "a.jsx" in result
        assert "b.tsx" in result
        assert "c.md" not in result

    def test_empty_list(self):
        assert filter_by_extensions([]) == []


class TestGetChangedFilesFiltered:
    def test_not_git_repo(self):
        with patch("infrastructure.git_diff_scanner.get_changed_files", return_value=None):
            result = get_changed_files_filtered(root=Path("/tmp"))
            assert result == []

    def test_filters_results(self):
        diff = DiffResult(
            added=["src/app.py", "README.md"],
            modified=["src/utils.js"],
            deleted=[],
            renamed=[],
        )
        with patch("infrastructure.git_diff_scanner.get_changed_files", return_value=diff):
            result = get_changed_files_filtered(root=Path("/tmp"))
            assert "src/app.py" in result
            assert "src/utils.js" in result
            assert "README.md" not in result
