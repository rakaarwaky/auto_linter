"""Comprehensive tests for lint_identifier_vo.py — 100% coverage."""

import pytest
from taxonomy.lint_identifier_vo import (
    AdapterName,
    FilePath,
    SymbolName,
    DirectoryPath,
)


# ─── AdapterName ─────────────────────────────────────────────────────────────

class TestAdapterName:
    def test_init(self):
        an = AdapterName(value="ruff")
        assert an.value == "ruff"

    def test_str(self):
        assert str(AdapterName(value="mypy")) == "mypy"

    def test_hash(self):
        an = AdapterName(value="ruff")
        assert hash(an) == hash("ruff")
        d = {an: "found"}
        assert d[AdapterName(value="ruff")] == "found"

    def test_eq_same_type(self):
        assert AdapterName(value="ruff") == AdapterName(value="ruff")
        assert not (AdapterName(value="ruff") == AdapterName(value="mypy"))

    def test_eq_str(self):
        assert AdapterName(value="ruff") == "ruff"
        assert not (AdapterName(value="ruff") == "mypy")

    def test_eq_other_type(self):
        assert AdapterName(value="ruff").__eq__(42) is NotImplemented

    def test_validation_empty(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            AdapterName(value="")

    def test_validation_whitespace(self):
        with pytest.raises(ValueError):
            AdapterName(value="   ")

    def test_strip_whitespace(self):
        an = AdapterName(value="  ruff  ")
        assert an.value == "ruff"

    def test_frozen(self):
        an = AdapterName(value="ruff")
        with pytest.raises(Exception):
            an.value = "mypy"

    def test_model_dump(self):
        an = AdapterName(value="bandit")
        assert an.model_dump() == {"value": "bandit"}


# ─── FilePath ────────────────────────────────────────────────────────────────

class TestFilePath:
    def test_init(self):
        fp = FilePath(value="src/app.py")
        assert fp.value == "src/app.py"

    def test_str(self):
        assert str(FilePath(value="src/app.py")) == "src/app.py"

    def test_hash(self):
        fp = FilePath(value="src/app.py")
        assert hash(fp) == hash("src/app.py")

    def test_eq_same_type(self):
        assert FilePath(value="src/app.py") == FilePath(value="src/app.py")
        assert not (FilePath(value="src/app.py") == FilePath(value="src/main.py"))

    def test_eq_str(self):
        assert FilePath(value="src/app.py") == "src/app.py"

    def test_eq_other_type(self):
        assert FilePath(value="src/app.py").__eq__(42) is NotImplemented

    def test_validation_empty(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            FilePath(value="")

    def test_validation_whitespace(self):
        with pytest.raises(ValueError):
            FilePath(value="   ")

    def test_strip_whitespace(self):
        fp = FilePath(value="  src/app.py  ")
        assert fp.value == "src/app.py"

    def test_backslash_to_forward(self):
        fp = FilePath(value="src\\app.py")
        assert fp.value == "src/app.py"

    def test_trailing_slash_removed(self):
        fp = FilePath(value="src/")
        assert fp.value == "src"

    def test_extension_py(self):
        assert FilePath(value="src/app.py").extension == "py"

    def test_extension_ts(self):
        assert FilePath(value="src/app.ts").extension == "ts"

    def test_extension_no_dot(self):
        # Makefile has no extension → empty string
        assert FilePath(value="Makefile").extension == ""

    def test_extension_dotfile(self):
        # Dotfiles like .gitignore → empty string
        assert FilePath(value=".gitignore").extension == ""

    def test_has_extension(self):
        assert FilePath(value="src/app.py").has_extension("py")
        assert not FilePath(value="src/app.py").has_extension("js")

    def test_has_extension_case_insensitive(self):
        assert FilePath(value="src/app.PY").has_extension("py")

    def test_frozen(self):
        fp = FilePath(value="src/app.py")
        with pytest.raises(Exception):
            fp.value = "src/main.py"


# ─── SymbolName ──────────────────────────────────────────────────────────────

class TestSymbolName:
    def test_init(self):
        sn = SymbolName(value="my_function")
        assert sn.value == "my_function"

    def test_str(self):
        assert str(SymbolName(value="CamelCase")) == "CamelCase"

    def test_hash(self):
        sn = SymbolName(value="func")
        assert hash(sn) == hash("func")

    def test_eq_same_type(self):
        assert SymbolName(value="func") == SymbolName(value="func")
        assert not (SymbolName(value="func") == SymbolName(value="other"))

    def test_eq_str(self):
        assert SymbolName(value="func") == "func"

    def test_eq_other_type(self):
        assert SymbolName(value="func").__eq__(42) is NotImplemented

    def test_validation_empty(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            SymbolName(value="")

    def test_validation_whitespace(self):
        with pytest.raises(ValueError):
            SymbolName(value="   ")

    def test_strip_whitespace(self):
        sn = SymbolName(value="  func  ")
        assert sn.value == "func"

    def test_frozen(self):
        sn = SymbolName(value="func")
        with pytest.raises(Exception):
            sn.value = "other"


# ─── DirectoryPath ───────────────────────────────────────────────────────────

class TestDirectoryPath:
    def test_init(self):
        dp = DirectoryPath(value="/home/user")
        assert dp.value == "/home/user"

    def test_str(self):
        assert str(DirectoryPath(value="/opt")) == "/opt"

    def test_hash(self):
        dp = DirectoryPath(value="/home")
        assert hash(dp) == hash("/home")

    def test_eq_same_type(self):
        assert DirectoryPath(value="/home") == DirectoryPath(value="/home")
        assert not (DirectoryPath(value="/home") == DirectoryPath(value="/opt"))

    def test_eq_str(self):
        assert DirectoryPath(value="/home") == "/home"

    def test_eq_other_type(self):
        assert DirectoryPath(value="/home").__eq__(42) is NotImplemented

    def test_validation_empty(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            DirectoryPath(value="")

    def test_validation_whitespace(self):
        with pytest.raises(ValueError):
            DirectoryPath(value="   ")

    def test_strip_whitespace(self):
        dp = DirectoryPath(value="  /home  ")
        assert dp.value == "/home"

    def test_backslash_to_forward(self):
        dp = DirectoryPath(value="home\\user")
        assert dp.value == "home/user"

    def test_trailing_slash_removed(self):
        dp = DirectoryPath(value="/home/")
        assert dp.value == "/home"

    def test_frozen(self):
        dp = DirectoryPath(value="/home")
        with pytest.raises(Exception):
            dp.value = "/opt"
