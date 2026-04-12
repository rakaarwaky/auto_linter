"""Tests for relative_path_resolver module."""
import os
from taxonomy.relative_path_resolver import normalize_path


class TestNormalizePath:
    """Tests for normalize_path function."""

    def test_empty_path_returns_empty(self):
        """Empty path should return empty string."""
        result = normalize_path("")
        assert result == ""

    def test_none_path_returns_none(self):
        """None path should return None."""
        result = normalize_path(None)
        assert result is None

    def test_backslash_converted_to_forward_slash(self):
        """Backslashes should be converted to forward slashes."""
        result = normalize_path("a\\b\\c.py")
        assert "\\" not in result
        assert "a/b/c.py" in result

    def test_double_slashes_reduced_to_single(self):
        """Double slashes should be reduced to single."""
        result = normalize_path("/home//user//file.py")
        assert "//" not in result
        assert "/home/user/file.py" == result

    def test_phantom_root_replacement(self, monkeypatch):
        """Phantom root should be replaced with actual root."""
        monkeypatch.setenv("PHANTOM_ROOT", "/phantom/")
        monkeypatch.setenv("PROJECT_ROOT", "/actual/")
        result = normalize_path("/phantom/src/file.py")
        assert result == "/actual/src/file.py"

    def test_no_phantom_root_unchanged(self, monkeypatch):
        """When phantom root not in path, path should be unchanged."""
        monkeypatch.delenv("PHANTOM_ROOT", raising=False)
        monkeypatch.delenv("PROJECT_ROOT", raising=False)
        result = normalize_path("/other/path/file.py")
        assert result == "/other/path/file.py"

    def test_src_prefix_made_absolute(self, monkeypatch, tmp_path):
        """src/ prefix should be made absolute when cwd contains auto_linter."""
        auto_linter_dir = tmp_path / "auto_linter"
        auto_linter_dir.mkdir()
        (auto_linter_dir / "src").mkdir()
        monkeypatch.chdir(auto_linter_dir)
        result = normalize_path("src/file.py")
        assert os.path.isabs(result)
        assert result.endswith("src/file.py")

    def test_dot_src_prefix_made_absolute(self, monkeypatch, tmp_path):
        """./src/ prefix should be made absolute when cwd contains auto_linter."""
        auto_linter_dir = tmp_path / "auto_linter"
        auto_linter_dir.mkdir()
        (auto_linter_dir / "src").mkdir()
        monkeypatch.chdir(auto_linter_dir)
        result = normalize_path("./src/file.py")
        assert os.path.isabs(result)

    def test_src_prefix_not_converted_outside_project(self, monkeypatch, tmp_path):
        """src/ prefix should stay relative when cwd doesn't contain auto_linter."""
        monkeypatch.chdir(tmp_path)
        result = normalize_path("src/file.py")
        assert result == "src/file.py"

    def test_non_project_path_unchanged(self, monkeypatch, tmp_path):
        """Non-project paths should not be modified."""
        monkeypatch.chdir(tmp_path)
        result = normalize_path("/other/project/file.py")
        assert result == "/other/project/file.py"

    def test_env_vars_override_defaults(self, monkeypatch):
        """Environment variables should override default values."""
        monkeypatch.setenv("PHANTOM_ROOT", "/custom/phantom/")
        monkeypatch.setenv("PROJECT_ROOT", "/custom/actual/")
        result = normalize_path("/custom/phantom/file.py")
        assert result == "/custom/actual/file.py"

    def test_dot_slash_src_not_converted_outside_project(self, monkeypatch, tmp_path):
        """./src/ should stay unchanged when cwd doesn't contain auto_linter."""
        monkeypatch.chdir(tmp_path)
        result = normalize_path("./src/file.py")
        assert result == "./src/file.py"

    def test_already_absolute_unchanged(self):
        """Already absolute non-project paths should be unchanged."""
        result = normalize_path("/home/user/project/file.py")
        assert result == "/home/user/project/file.py"
