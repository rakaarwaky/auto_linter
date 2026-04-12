"""Comprehensive tests for infrastructure/path_normalization_util.py — 100% coverage."""

import os
from unittest.mock import patch
from infrastructure.path_normalization_util import normalize_path


class TestNormalizePath:
    def test_none(self):
        assert normalize_path(None) is None

    def test_empty_string(self):
        assert normalize_path("") == ""

    @patch.dict(os.environ, {"PHANTOM_ROOT": "/not_in_use/", "PROJECT_ROOT": "/actual/"})
    def test_backslash_to_forward(self):
        # Note: in auto_linter cwd, "src/" paths get absolutized
        result = normalize_path("src\\app.py")
        assert result == "src/app.py" or result.endswith("src/app.py")

    @patch.dict(os.environ, {"PHANTOM_ROOT": "/not_in_use/", "PROJECT_ROOT": "/actual/"})
    def test_double_slash_to_single(self):
        result = normalize_path("src//app.py")
        assert result == "src/app.py" or result.endswith("src/app.py")

    @patch.dict(os.environ, {"PHANTOM_ROOT": "/not_in_use/", "PROJECT_ROOT": "/actual/"})
    def test_no_change_absolute(self):
        result = normalize_path("/some/path/app.py")
        assert result == "/some/path/app.py"

    @patch.dict(os.environ, {"PHANTOM_ROOT": "/home/raka/src/", "PROJECT_ROOT": "/actual/"})
    def test_phantom_root_replacement(self):
        result = normalize_path("/home/raka/src/app.py")
        assert "/home/raka/src/" not in result
        assert "/actual/" in result

    @patch.dict(os.environ, {"PHANTOM_ROOT": "/phantom/", "PROJECT_ROOT": "/real/"})
    def test_no_phantom_in_path(self):
        result = normalize_path("/other/src/app.py")
        assert result == "/other/src/app.py"

    @patch.dict(os.environ, {"PHANTOM_ROOT": "/home/raka/src/", "PROJECT_ROOT": "/persistent/home/raka/mcp-servers/auto_linter/src/"})
    def test_phantom_root_default(self):
        result = normalize_path("/home/raka/src/app.py")
        assert "/persistent/" in result

    @patch.dict(os.environ, {"PHANTOM_ROOT": "/not_in_use/", "PROJECT_ROOT": "/actual/"})
    def test_dot_src_path(self, monkeypatch):
        monkeypatch.chdir("/tmp")
        result = normalize_path("./src/app.py")
        assert result == "./src/app.py"

    @patch.dict(os.environ, {"PHANTOM_ROOT": "/not_in_use/", "PROJECT_ROOT": "/actual/"})
    def test_dot_dot_path(self, monkeypatch):
        monkeypatch.chdir("/tmp")
        result = normalize_path("../src/app.py")
        assert result == "../src/app.py"
