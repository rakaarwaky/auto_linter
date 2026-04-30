"""Comprehensive tests for lint_adapter_error.py — 100% coverage."""

import pytest
from taxonomy.lint_value_vo import ErrorCode
from taxonomy.lint_identifier_vo import FilePath, AdapterName
from taxonomy.lint_domain_vo import CommandArgs
from taxonomy.lint_adapter_error import (
    AdapterError,
    ScanError,
    ValidationError,
)


# ─── AdapterError ────────────────────────────────────────────────────────────

class TestAdapterError:
    def test_init(self):
        err = AdapterError(
            adapter_name=AdapterName(value="ruff"),
            message="Command failed"
        )
        assert str(err.adapter_name) == "ruff"
        assert err.message == "Command failed"
        assert err.error_code is None
        assert err.stderr == ""
        assert err.exit_code is None

    def test_with_error_code(self):
        ec = ErrorCode(code="E501")
        err = AdapterError(
            adapter_name=AdapterName(value="ruff"),
            message="Line too long",
            error_code=ec
        )
        assert err.error_code == ec

    def test_with_command(self):
        cmd = CommandArgs(args=["ruff", "check", "."])
        err = AdapterError(
            adapter_name=AdapterName(value="ruff"),
            message="Failed",
            command=cmd,
            stderr="error output",
            exit_code=1
        )
        assert err.stderr == "error output"
        assert err.exit_code == 1

    def test_str_without_code(self):
        err = AdapterError(
            adapter_name=AdapterName(value="ruff"),
            message="Command failed"
        )
        assert str(err) == "[ruff] Command failed"

    def test_str_with_code(self):
        ec = ErrorCode(code="E501")
        err = AdapterError(
            adapter_name=AdapterName(value="ruff"),
            message="Line too long",
            error_code=ec
        )
        assert str(err) == "[ruff] [E501] Line too long"

    def test_model_dump(self):
        err = AdapterError(
            adapter_name=AdapterName(value="ruff"),
            message="Failed"
        )
        dump = err.model_dump()
        assert dump["message"] == "Failed"
        assert "adapter_name" in dump

    def test_frozen(self):
        err = AdapterError(
            adapter_name=AdapterName(value="ruff"),
            message="Failed"
        )
        with pytest.raises(Exception):
            err.message = "Changed"


# ─── ScanError ───────────────────────────────────────────────────────────────

class TestScanError:
    def test_init(self):
        err = ScanError(
            path=FilePath(value="src/app.py"),
            message="Scan failed"
        )
        assert str(err.path) == "src/app.py"
        assert err.message == "Scan failed"
        assert err.adapter_name is None
        assert err.cause is None

    def test_with_adapter(self):
        err = ScanError(
            path=FilePath(value="src/app.py"),
            message="Timeout",
            adapter_name=AdapterName(value="mypy"),
            cause="Network error"
        )
        assert err.adapter_name == AdapterName(value="mypy")
        assert err.cause == "Network error"

    def test_with_error_code(self):
        ec = ErrorCode(code="E902")
        err = ScanError(
            path=FilePath(value="src/app.py"),
            message="File not found",
            error_code=ec
        )
        assert err.error_code == ec

    def test_str_no_adapter(self):
        err = ScanError(
            path=FilePath(value="src/app.py"),
            message="Failed"
        )
        assert str(err) == "Scan failed: src/app.py — Failed"

    def test_str_with_adapter(self):
        err = ScanError(
            path=FilePath(value="src/app.py"),
            message="Failed",
            adapter_name=AdapterName(value="mypy")
        )
        assert str(err) == "Scan failed (mypy): src/app.py — Failed"

    def test_str_with_code(self):
        ec = ErrorCode(code="E902")
        err = ScanError(
            path=FilePath(value="src/app.py"),
            message="Missing",
            error_code=ec
        )
        assert str(err) == "Scan failed [E902]: src/app.py — Missing"

    def test_model_dump(self):
        err = ScanError(
            path=FilePath(value="src/app.py"),
            message="Failed"
        )
        dump = err.model_dump()
        assert dump["path"]["value"] == "src/app.py"
        assert dump["message"] == "Failed"

    def test_frozen(self):
        err = ScanError(
            path=FilePath(value="src/app.py"),
            message="Failed"
        )
        with pytest.raises(Exception):
            err.message = "Changed"


# ─── ValidationError ─────────────────────────────────────────────────────────

class TestValidationError:
    def test_init(self):
        err = ValidationError(
            field_name="score",
            message="Must be a number"
        )
        assert err.field_name == "score"
        assert err.message == "Must be a number"
        assert err.constraint == ""
        assert err.value == ""

    def test_full_init(self):
        err = ValidationError(
            field_name="threshold",
            message="Out of range",
            constraint="0-100",
            value="150"
        )
        assert err.constraint == "0-100"
        assert err.value == "150"

    def test_str(self):
        err = ValidationError(
            field_name="score",
            message="Must be a number"
        )
        assert str(err) == "Validation failed on 'score': Must be a number"

    def test_model_dump(self):
        err = ValidationError(
            field_name="score",
            message="Required"
        )
        dump = err.model_dump()
        assert dump["field_name"] == "score"
        assert dump["message"] == "Required"

    def test_frozen(self):
        err = ValidationError(
            field_name="score",
            message="Required"
        )
        with pytest.raises(Exception):
            err.message = "Changed"
