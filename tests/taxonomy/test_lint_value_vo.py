"""Comprehensive tests for lint_value_vo.py — 100% coverage."""

import pytest
from taxonomy.lint_value_vo import (
    Severity,
    ErrorCode,
    Position,
    Score,
    FileFormat,
    FORMAT_TEXT,
    FORMAT_JSON,
    FORMAT_SARIF,
    FORMAT_JUNIT,
    ALL_FORMATS,
)


# ─── Severity ────────────────────────────────────────────────────────────────

class TestSeverity:
    def test_severity_values(self):
        assert Severity.INFO.value == "info"
        assert Severity.LOW.value == "low"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.HIGH.value == "high"
        assert Severity.CRITICAL.value == "critical"

    def test_severity_score_impact(self):
        assert Severity.INFO.score_impact == 0
        assert Severity.LOW.score_impact == 0
        assert Severity.MEDIUM.score_impact == 2
        assert Severity.HIGH.score_impact == 10
        assert Severity.CRITICAL.score_impact == 50

    def test_severity_is_str_enum(self):
        # str+Enum = auto serializes as string
        assert str(Severity.HIGH) == "Severity.HIGH"
        assert Severity.HIGH == "high"

    def test_severity_from_string(self):
        assert Severity("info") == Severity.INFO
        assert Severity("low") == Severity.LOW
        assert Severity("medium") == Severity.MEDIUM
        assert Severity("high") == Severity.HIGH
        assert Severity("critical") == Severity.CRITICAL

    def test_severity_hashable(self):
        d = {Severity.HIGH: "high_impact"}
        assert d[Severity.HIGH] == "high_impact"


# ─── ErrorCode ───────────────────────────────────────────────────────────────

class TestErrorCode:
    def test_init(self):
        ec = ErrorCode(code="E501")
        assert ec.code == "E501"

    def test_str(self):
        assert str(ErrorCode(code="F841")) == "F841"

    def test_is_style(self):
        assert ErrorCode(code="E501").is_style
        assert ErrorCode(code="W291").is_style
        assert ErrorCode(code="D100").is_style
        assert not ErrorCode(code="F841").is_style

    def test_is_logic(self):
        assert ErrorCode(code="F841").is_logic
        assert ErrorCode(code="I001").is_logic
        assert not ErrorCode(code="E501").is_logic

    def test_is_security(self):
        assert ErrorCode(code="B101").is_security
        assert not ErrorCode(code="E501").is_security

    def test_is_governance(self):
        assert ErrorCode(code="AES001").is_governance
        assert not ErrorCode(code="E501").is_governance

    def test_frozen(self):
        ec = ErrorCode(code="E501")
        with pytest.raises(Exception):
            ec.code = "F841"

    def test_model_dump(self):
        ec = ErrorCode(code="E501")
        assert ec.model_dump() == {"code": "E501"}

    def test_model_validate(self):
        ec = ErrorCode.model_validate({"code": "F841"})
        assert ec.code == "F841"


# ─── Position ────────────────────────────────────────────────────────────────

class TestPosition:
    def test_init_default_column(self):
        pos = Position(line=10)
        assert pos.line == 10
        assert pos.column == 0

    def test_init_with_column(self):
        pos = Position(line=10, column=5)
        assert pos.line == 10
        assert pos.column == 5

    def test_str_with_column(self):
        assert str(Position(line=10, column=5)) == "10:5"

    def test_str_without_column(self):
        assert str(Position(line=10)) == "10"

    def test_frozen(self):
        pos = Position(line=10)
        with pytest.raises(Exception):
            pos.line = 20


# ─── Score ───────────────────────────────────────────────────────────────────

class TestScore:
    def test_init(self):
        s = Score(value=85.0)
        assert s.value == 85.0

    def test_str(self):
        assert str(Score(value=85.5)) == "85.5"
        assert str(Score(value=100.0)) == "100.0"

    def test_is_passing(self):
        assert Score(value=80.0).is_passing
        assert Score(value=85.0).is_passing
        assert Score(value=100.0).is_passing
        assert not Score(value=79.9).is_passing
        assert not Score(value=0.0).is_passing

    def test_is_perfect(self):
        assert Score(value=100.0).is_perfect
        assert not Score(value=99.9).is_perfect

    def test_deduct(self):
        s = Score(value=100.0)
        s2 = s.deduct(Severity.HIGH)
        assert s2.value == 90.0

    def test_deduct_medium(self):
        s = Score(value=10.0)
        s2 = s.deduct(Severity.MEDIUM)
        assert s2.value == 8.0

    def test_deduct_does_not_go_negative(self):
        s = Score(value=1.0)
        s2 = s.deduct(Severity.CRITICAL)
        assert s2.value == 0.0

    def test_deduct_low_no_change(self):
        s = Score(value=100.0)
        s2 = s.deduct(Severity.LOW)
        assert s2.value == 100.0

    def test_validation_below_range(self):
        with pytest.raises(ValueError):
            Score(value=-1.0)

    def test_validation_above_range(self):
        with pytest.raises(ValueError):
            Score(value=101.0)

    def test_validation_boundaries(self):
        assert Score(value=0.0).value == 0.0
        assert Score(value=100.0).value == 100.0

    def test_frozen(self):
        s = Score(value=50.0)
        with pytest.raises(Exception):
            s.value = 60.0


# ─── FileFormat ──────────────────────────────────────────────────────────────

class TestFileFormat:
    def test_init(self):
        ff = FileFormat(name="json")
        assert ff.name == "json"

    def test_str(self):
        assert str(FileFormat(name="text")) == "text"

    def test_is_structured(self):
        assert FileFormat(name="json").is_structured
        assert FileFormat(name="sarif").is_structured
        assert FileFormat(name="junit").is_structured
        assert not FileFormat(name="text").is_structured

    def test_frozen(self):
        ff = FileFormat(name="json")
        with pytest.raises(Exception):
            ff.name = "xml"


# ─── Format constants ────────────────────────────────────────────────────────

class TestFormatConstants:
    def test_format_text(self):
        assert FORMAT_TEXT.name == "text"
        assert not FORMAT_TEXT.is_structured

    def test_format_json(self):
        assert FORMAT_JSON.name == "json"
        assert FORMAT_JSON.is_structured

    def test_format_sarif(self):
        assert FORMAT_SARIF.name == "sarif"
        assert FORMAT_SARIF.is_structured

    def test_format_junit(self):
        assert FORMAT_JUNIT.name == "junit"
        assert FORMAT_JUNIT.is_structured

    def test_all_formats(self):
        assert len(ALL_FORMATS) == 4
        assert FORMAT_TEXT in ALL_FORMATS
        assert FORMAT_JSON in ALL_FORMATS
        assert FORMAT_SARIF in ALL_FORMATS
        assert FORMAT_JUNIT in ALL_FORMATS
