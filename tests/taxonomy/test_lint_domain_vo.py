"""Comprehensive tests for lint_domain_vo.py — 100% coverage."""

import pytest
from taxonomy.lint_domain_vo import (
    ScopeRef,
    Location,
    ViolationConstraint,
    CommandArgs,
)


# ─── ScopeRef ────────────────────────────────────────────────────────────────

class TestScopeRef:
    def test_init_defaults(self):
        sr = ScopeRef(name="processPayment")
        assert sr.name == "processPayment"
        assert sr.kind == "function"
        assert sr.file == ""
        assert sr.start_line == 0
        assert sr.end_line == 0

    def test_init_with_kind(self):
        sr = ScopeRef(name="PaymentService", kind="class")
        assert sr.kind == "class"

    def test_init_with_file(self):
        sr = ScopeRef(name="run_scan", kind="function", file="src/scan.py",
                      start_line=10, end_line=50)
        assert sr.file == "src/scan.py"
        assert sr.start_line == 10
        assert sr.end_line == 50

    def test_str_without_file(self):
        assert str(ScopeRef(name="my_func")) == "function my_func"

    def test_str_with_file(self):
        sr = ScopeRef(name="my_func", kind="function", file="src/app.py")
        assert str(sr) == "function my_func in src/app.py"

    def test_str_class(self):
        sr = ScopeRef(name="MyClass", kind="class", file="src/models.py")
        assert str(sr) == "class MyClass in src/models.py"

    def test_str_no_kind(self):
        sr = ScopeRef(name="raw_ref", kind="")
        assert str(sr) == "raw_ref"

    def test_has_range_false(self):
        assert not ScopeRef(name="func").has_range

    def test_has_range_true(self):
        sr = ScopeRef(name="func", start_line=1, end_line=10)
        assert sr.has_range

    def test_validation_empty(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            ScopeRef(name="")

    def test_validation_whitespace(self):
        with pytest.raises(ValueError):
            ScopeRef(name="   ")

    def test_strip_whitespace(self):
        sr = ScopeRef(name="  func  ")
        assert sr.name == "func"

    def test_frozen(self):
        sr = ScopeRef(name="func")
        with pytest.raises(Exception):
            sr.name = "other"


# ─── Location ────────────────────────────────────────────────────────────────

class TestLocation:
    def test_init_defaults(self):
        loc = Location()
        assert loc.file == ""
        assert loc.line == 0
        assert loc.column == 0
        assert loc.description == ""

    def test_init_full(self):
        loc = Location(file="src/app.py", line=42, column=5,
                       description="unused import")
        assert loc.file == "src/app.py"
        assert loc.line == 42
        assert loc.column == 5
        assert loc.description == "unused import"

    def test_str_full(self):
        loc = Location(file="src/app.py", line=42, column=5)
        assert str(loc) == "src/app.py:42:5"

    def test_str_line_only(self):
        loc = Location(file="src/app.py", line=42)
        assert str(loc) == "src/app.py:42"

    def test_str_with_description(self):
        loc = Location(file="src/app.py", line=42, description="unused import")
        assert str(loc) == "src/app.py:42 — unused import"

    def test_str_line_and_col_with_description(self):
        loc = Location(file="src/app.py", line=42, column=5, description="unused import")
        assert str(loc) == "src/app.py:42:5 — unused import"

    def test_str_unknown(self):
        loc = Location()
        assert str(loc) == "unknown"

    def test_frozen(self):
        loc = Location(file="src/app.py", line=10)
        with pytest.raises(Exception):
            loc.line = 20


# ─── ViolationConstraint ─────────────────────────────────────────────────────

class TestViolationConstraint:
    def test_init_defaults(self):
        vc = ViolationConstraint(rule="min_length")
        assert vc.rule == "min_length"
        assert vc.min_value == ""
        assert vc.max_value == ""

    def test_init_with_range(self):
        vc = ViolationConstraint(rule="score_range", min_value="0", max_value="100")
        assert vc.min_value == "0"
        assert vc.max_value == "100"

    def test_str_rule_only(self):
        assert str(ViolationConstraint(rule="not_empty")) == "not_empty"

    def test_str_with_min_only(self):
        vc = ViolationConstraint(rule="min_length", min_value="1")
        assert str(vc) == "min_length (must be 1)"

    def test_str_with_max_only(self):
        vc = ViolationConstraint(rule="max_length", max_value="100")
        assert str(vc) == "max_length (must be 100)"

    def test_str_with_range(self):
        vc = ViolationConstraint(rule="score_range", min_value="0", max_value="100")
        assert str(vc) == "score_range (must be 0..100)"

    def test_frozen(self):
        vc = ViolationConstraint(rule="test")
        with pytest.raises(Exception):
            vc.rule = "other"


# ─── CommandArgs ─────────────────────────────────────────────────────────────

class TestCommandArgs:
    def test_init_empty(self):
        ca = CommandArgs()
        assert ca.args == []

    def test_init_with_args(self):
        ca = CommandArgs(args=["ruff", "check", "."])
        assert ca.args == ["ruff", "check", "."]

    def test_str_empty(self):
        assert str(CommandArgs()) == ""

    def test_str_with_args(self):
        assert str(CommandArgs(args=["ruff", "check", "."])) == "ruff check ."

    def test_len_empty(self):
        assert len(CommandArgs()) == 0

    def test_len_with_args(self):
        assert len(CommandArgs(args=["a", "b", "c"])) == 3

    def test_frozen(self):
        ca = CommandArgs(args=["ruff"])
        with pytest.raises(Exception):
            ca.args = ["other"]
