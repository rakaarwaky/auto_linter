"""Comprehensive tests for lint_scan_event.py — 100% coverage."""

import pytest
from datetime import datetime, timezone
from taxonomy.lint_value_vo import Severity, ErrorCode, Score
from taxonomy.lint_identifier_vo import FilePath, AdapterName
from taxonomy.lint_scan_event import (
    ScanStarted,
    ScanCompleted,
    ScanFailed,
    FixApplied,
    AdapterRegistered,
    HookInstalled,
    HookRemoved,
)


# ─── ScanStarted ─────────────────────────────────────────────────────────────

class TestScanStarted:
    def test_init(self):
        ev = ScanStarted(
            path=FilePath(value="src/"),
            adapters=[AdapterName(value="ruff")]
        )
        assert str(ev.path) == "src"
        assert ev.adapters[0] == AdapterName(value="ruff")

    def test_auto_timestamp(self):
        ev = ScanStarted(
            path=FilePath(value="src/"),
            adapters=[AdapterName(value="ruff")]
        )
        assert ev.timestamp != ""
        # Verify it's valid ISO format
        datetime.fromisoformat(ev.timestamp)

    def test_custom_timestamp(self):
        ev = ScanStarted(
            path=FilePath(value="src/"),
            adapters=[AdapterName(value="ruff")],
            timestamp="2026-01-01T00:00:00"
        )
        assert ev.timestamp == "2026-01-01T00:00:00"

    def test_multiple_adapters(self):
        ev = ScanStarted(
            path=FilePath(value="src/"),
            adapters=[AdapterName(value="ruff"), AdapterName(value="mypy")]
        )
        assert len(ev.adapters) == 2

    def test_frozen(self):
        ev = ScanStarted(
            path=FilePath(value="src/"),
            adapters=[AdapterName(value="ruff")]
        )
        with pytest.raises(Exception):
            ev.path = FilePath(value="other/")


# ─── ScanCompleted ────────────────────────────────────────────────────────────

class TestScanCompleted:
    def test_init(self):
        ev = ScanCompleted(
            path=FilePath(value="src/"),
            score=Score(value=95.0),
            worst_severity=Severity.LOW,
            violation_count=3,
            duration_ms=1500.0
        )
        assert str(ev.path) == "src"
        assert ev.score.value == 95.0
        assert ev.worst_severity == Severity.LOW
        assert ev.violation_count == 3
        assert ev.duration_ms == 1500.0

    def test_is_passing(self):
        ev = ScanCompleted(
            path=FilePath(value="src/"),
            score=Score(value=85.0),
            worst_severity=Severity.LOW,
            violation_count=0,
            duration_ms=1000.0
        )
        assert ev.is_passing

    def test_auto_timestamp(self):
        ev = ScanCompleted(
            path=FilePath(value="src/"),
            score=Score(value=90.0),
            worst_severity=Severity.MEDIUM,
            violation_count=1,
            duration_ms=500.0
        )
        assert ev.timestamp != ""
        datetime.fromisoformat(ev.timestamp)

    def test_frozen(self):
        ev = ScanCompleted(
            path=FilePath(value="src/"),
            score=Score(value=100.0),
            worst_severity=Severity.INFO,
            violation_count=0,
            duration_ms=0
        )
        with pytest.raises(Exception):
            ev.score = Score(value=50.0)


# ─── ScanFailed ──────────────────────────────────────────────────────────────

class TestScanFailed:
    def test_init(self):
        ev = ScanFailed(
            path=FilePath(value="src/"),
            adapter=AdapterName(value="mypy"),
            error_message="Config file not found"
        )
        assert str(ev.adapter) == "mypy"
        assert ev.error_message == "Config file not found"
        assert ev.error_code is None

    def test_with_error_code(self):
        ec = ErrorCode(code="E902")
        ev = ScanFailed(
            path=FilePath(value="src/"),
            adapter=AdapterName(value="ruff"),
            error_message="File not found",
            error_code=ec
        )
        assert ev.error_code == ec

    def test_auto_timestamp(self):
        ev = ScanFailed(
            path=FilePath(value="src/"),
            adapter=AdapterName(value="bandit"),
            error_message="Failed"
        )
        assert ev.timestamp != ""
        datetime.fromisoformat(ev.timestamp)

    def test_frozen(self):
        ev = ScanFailed(
            path=FilePath(value="src/"),
            adapter=AdapterName(value="ruff"),
            error_message="Error"
        )
        with pytest.raises(Exception):
            ev.error_message = "New error"


# ─── FixApplied ──────────────────────────────────────────────────────────────

class TestFixApplied:
    def test_init(self):
        ec = ErrorCode(code="F841")
        ev = FixApplied(
            path=FilePath(value="src/app.py"),
            adapter=AdapterName(value="ruff"),
            error_code=ec,
            changes_count=2
        )
        assert str(ev.path) == "src/app.py"
        assert str(ev.adapter) == "ruff"
        assert ev.error_code == ec
        assert ev.changes_count == 2

    def test_auto_timestamp(self):
        ec = ErrorCode(code="E501")
        ev = FixApplied(
            path=FilePath(value="src/app.py"),
            adapter=AdapterName(value="ruff"),
            error_code=ec,
            changes_count=1
        )
        assert ev.timestamp != ""
        datetime.fromisoformat(ev.timestamp)

    def test_frozen(self):
        ec = ErrorCode(code="W291")
        ev = FixApplied(
            path=FilePath(value="src/app.py"),
            adapter=AdapterName(value="ruff"),
            error_code=ec,
            changes_count=1
        )
        with pytest.raises(Exception):
            ev.changes_count = 5


# ─── AdapterRegistered ───────────────────────────────────────────────────────

class TestAdapterRegistered:
    def test_init(self):
        ev = AdapterRegistered(adapter_name=AdapterName(value="eslint"))
        assert str(ev.adapter_name) == "eslint"

    def test_auto_timestamp(self):
        ev = AdapterRegistered(adapter_name=AdapterName(value="prettier"))
        assert ev.timestamp != ""
        datetime.fromisoformat(ev.timestamp)

    def test_frozen(self):
        ev = AdapterRegistered(adapter_name=AdapterName(value="ruff"))
        with pytest.raises(Exception):
            ev.adapter_name = AdapterName(value="mypy")


# ─── HookInstalled ───────────────────────────────────────────────────────────

class TestHookInstalled:
    def test_init(self):
        ev = HookInstalled(
            path=FilePath(value="/project"),
            executable=FilePath(value="/usr/bin/auto-lint")
        )
        assert str(ev.path) == "/project"
        assert str(ev.executable) == "/usr/bin/auto-lint"

    def test_auto_timestamp(self):
        ev = HookInstalled(
            path=FilePath(value="/project"),
            executable=FilePath(value="auto-lint")
        )
        assert ev.timestamp != ""
        datetime.fromisoformat(ev.timestamp)

    def test_frozen(self):
        ev = HookInstalled(
            path=FilePath(value="/project"),
            executable=FilePath(value="auto-lint")
        )
        with pytest.raises(Exception):
            ev.path = FilePath(value="/other")


# ─── HookRemoved ─────────────────────────────────────────────────────────────

class TestHookRemoved:
    def test_init(self):
        ev = HookRemoved(path=FilePath(value="/project"))
        assert str(ev.path) == "/project"

    def test_auto_timestamp(self):
        ev = HookRemoved(path=FilePath(value="/project"))
        assert ev.timestamp != ""
        datetime.fromisoformat(ev.timestamp)

    def test_frozen(self):
        ev = HookRemoved(path=FilePath(value="/project"))
        with pytest.raises(Exception):
            ev.path = FilePath(value="/other")

    def test_model_dump(self):
        ev = HookRemoved(path=FilePath(value="/project"))
        dump = ev.model_dump()
        assert "path" in dump
        assert "timestamp" in dump
