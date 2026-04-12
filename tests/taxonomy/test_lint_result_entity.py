"""Comprehensive tests for lint_result_entity.py — 100% coverage."""

import pytest
from taxonomy.lint_value_vo import Severity, ErrorCode, Position, Score
from taxonomy.lint_identifier_vo import FilePath, AdapterName
from taxonomy.lint_domain_vo import ScopeRef, Location
from taxonomy.lint_result_entity import (
    LintResult,
    GovernanceReport,
    ILinterAdapter,
    ISemanticTracer,
    IHookManager,
)


# ─── LintResult ──────────────────────────────────────────────────────────────

class TestLintResult:
    def test_init_minimal(self):
        lr = LintResult(file="src/app.py", line=10)
        assert str(lr.file) == "src/app.py"
        assert lr.line == 10
        assert lr.column == 0
        assert lr.code == ""
        assert lr.message == ""
        assert lr.source is None
        assert lr.severity == Severity.MEDIUM
        assert lr.enclosing_scope is None
        assert lr.related_locations == []

    def test_init_full(self):
        lr = LintResult(
            file="src/app.py",
            line=10,
            column=5,
            code="F841",
            message="unused variable",
            source="ruff",
            severity=Severity.HIGH,
        )
        assert lr.column == 5
        assert lr.code == "F841"
        assert lr.message == "unused variable"
        assert lr.source == AdapterName(value="ruff")
        assert lr.severity == Severity.HIGH

    def test_file_auto_wrap_str(self):
        lr = LintResult(file="src/app.py", line=1)
        assert isinstance(lr.file, FilePath)
        assert lr.file.value == "src/app.py"

    def test_file_auto_wrap_filepath(self):
        lr = LintResult(file=FilePath(value="src/app.py"), line=1)
        assert isinstance(lr.file, FilePath)

    def test_source_auto_wrap_str(self):
        lr = LintResult(file="src/app.py", line=1, source="ruff")
        assert isinstance(lr.source, AdapterName)
        assert lr.source.value == "ruff"

    def test_source_auto_wrap_adaptername(self):
        lr = LintResult(file="src/app.py", line=1, source=AdapterName(value="mypy"))
        assert lr.source == AdapterName(value="mypy")

    def test_related_locations_auto_wrap_str(self):
        lr = LintResult(
            file="src/app.py",
            line=1,
            related_locations=["Caller: main()", "Called by: init()"]
        )
        assert all(isinstance(loc, Location) for loc in lr.related_locations)
        assert lr.related_locations[0].description == "Caller: main()"

    def test_related_locations_auto_wrap_location(self):
        loc = Location(file="src/app.py", line=5)
        lr = LintResult(
            file="src/app.py",
            line=1,
            related_locations=[loc]
        )
        assert lr.related_locations[0] == loc

    def test_position_property(self):
        lr = LintResult(file="src/app.py", line=10, column=5)
        pos = lr.position
        assert isinstance(pos, Position)
        assert pos.line == 10
        assert pos.column == 5

    def test_error_code_property(self):
        lr = LintResult(file="src/app.py", line=1, code="F841")
        ec = lr.error_code
        assert isinstance(ec, ErrorCode)
        assert ec.code == "F841"

    def test_identity(self):
        lr = LintResult(file="src/app.py", line=10, code="F841", source="ruff")
        assert lr.identity == "src/app.py:10:F841:ruff"

    def test_enrich_enclosing_scope(self):
        lr = LintResult(file="src/app.py", line=10)
        scope = ScopeRef(name="my_func", kind="function")
        lr.enrich(enclosing_scope=scope)
        assert lr.enclosing_scope == scope

    def test_enrich_related(self):
        lr = LintResult(file="src/app.py", line=10)
        loc = Location(file="src/app.py", line=5)
        lr.enrich(related=[loc])
        assert loc in lr.related_locations

    def test_enrich_both(self):
        lr = LintResult(file="src/app.py", line=10)
        scope = ScopeRef(name="my_func")
        loc = Location(file="src/app.py", line=5)
        lr.enrich(enclosing_scope=scope, related=[loc])
        assert lr.enclosing_scope == scope
        assert loc in lr.related_locations


# ─── GovernanceReport ────────────────────────────────────────────────────────

class TestGovernanceReport:
    def test_init_defaults(self):
        gr = GovernanceReport()
        assert gr.results == []
        assert gr.score == 100.0
        assert gr.is_passing is True

    def test_add_result_medium(self):
        gr = GovernanceReport()
        lr = LintResult(file="src/app.py", line=10, severity=Severity.MEDIUM)
        gr.add_result(lr)
        assert len(gr.results) == 1
        assert gr.score == 98.0
        assert gr.is_passing is True

    def test_add_result_high(self):
        gr = GovernanceReport()
        lr = LintResult(file="src/app.py", line=10, severity=Severity.HIGH)
        gr.add_result(lr)
        assert gr.score == 90.0
        assert gr.is_passing is True

    def test_add_result_critical(self):
        gr = GovernanceReport()
        lr = LintResult(file="src/app.py", line=10, severity=Severity.CRITICAL)
        gr.add_result(lr)
        assert gr.score == 50.0
        assert gr.is_passing is False

    def test_add_result_multiple(self):
        gr = GovernanceReport()
        gr.add_result(LintResult(file="a.py", line=1, severity=Severity.MEDIUM))
        gr.add_result(LintResult(file="b.py", line=1, severity=Severity.MEDIUM))
        assert gr.score == 96.0

    def test_add_result_does_not_go_negative(self):
        gr = GovernanceReport()
        for _ in range(3):
            gr.add_result(LintResult(file="a.py", line=1, severity=Severity.CRITICAL))
        assert gr.score == 0.0

    def test_results_by_source(self):
        gr = GovernanceReport()
        gr.add_result(LintResult(file="a.py", line=1, source="ruff"))
        gr.add_result(LintResult(file="b.py", line=1, source="mypy"))
        gr.add_result(LintResult(file="c.py", line=1, source="ruff"))

        ruff = gr.results_by_source("ruff")
        assert len(ruff) == 2

        mypy = gr.results_by_source("mypy")
        assert len(mypy) == 1

    def test_violation_count(self):
        gr = GovernanceReport()
        gr.add_result(LintResult(file="a.py", line=1, severity=Severity.MEDIUM))
        gr.add_result(LintResult(file="b.py", line=1, severity=Severity.INFO))
        assert gr.violation_count == 1

    def test_sources_unique(self):
        gr = GovernanceReport()
        gr.add_result(LintResult(file="a.py", line=1, source="ruff"))
        gr.add_result(LintResult(file="b.py", line=1, source="ruff"))
        gr.add_result(LintResult(file="c.py", line=1, source="mypy"))
        assert gr.sources == ["ruff", "mypy"]


# ─── Interface Tests ─────────────────────────────────────────────────────────

class TestInterfaces:
    def test_ilinter_adapter_is_abstract(self):
        with pytest.raises(TypeError):
            ILinterAdapter()

    def test_isemantic_tracer_is_abstract(self):
        with pytest.raises(TypeError):
            ISemanticTracer()

    def test_ihook_manager_is_abstract(self):
        with pytest.raises(TypeError):
            IHookManager()
