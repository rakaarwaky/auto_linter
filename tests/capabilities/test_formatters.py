"""Tests for SARIF and JUnit report formatters."""
import json
from capabilities.linting_report_formatters import to_sarif, to_junit


SAMPLE_RESULTS = {
    "ruff": [
        {
            "file": "test.py",
            "line": 10,
            "code": "E501",
            "message": "Line too long",
            "severity": "medium",
            "column": 5,
            "enclosing_scope": "def main",
            "related_locations": [],
        },
        {
            "file": "test.py",
            "line": 20,
            "code": "F401",
            "message": "Unused import",
            "severity": "high",
            "column": 1,
            "enclosing_scope": None,
            "related_locations": [],
        },
    ],
    "mypy": [
        {
            "file": "app.py",
            "line": 5,
            "code": "type-error",
            "message": "Incompatible types",
            "severity": "high",
            "column": 0,
            "enclosing_scope": None,
            "related_locations": [],
        }
    ],
    "governance": [],
    "score": 80.0,
    "is_passing": False,
    "summary": {"ruff": 2, "mypy": 1, "governance": 0},
}


class TestSarifFormatter:
    def test_valid_sarif_output(self):
        result = to_sarif(SAMPLE_RESULTS)
        data = json.loads(result)
        assert data["version"] == "2.1.0"
        assert "$schema" in data
        assert len(data["runs"]) == 1

    def test_sarif_contains_all_results(self):
        result = to_sarif(SAMPLE_RESULTS)
        data = json.loads(result)
        sarif_results = data["runs"][0]["results"]
        # ruff (2) + mypy (1) = 3
        assert len(sarif_results) == 3

    def test_sarif_rule_id_format(self):
        result = to_sarif(SAMPLE_RESULTS)
        data = json.loads(result)
        sarif_results = data["runs"][0]["results"]
        rule_ids = [r["ruleId"] for r in sarif_results]
        assert "ruff/E501" in rule_ids
        assert "ruff/F401" in rule_ids
        assert "mypy/type-error" in rule_ids

    def test_sarif_severity_mapping(self):
        result = to_sarif(SAMPLE_RESULTS)
        data = json.loads(result)
        sarif_results = data["runs"][0]["results"]
        levels = {r["ruleId"]: r["level"] for r in sarif_results}
        assert levels["ruff/E501"] == "warning"   # medium
        assert levels["ruff/F401"] == "error"      # high
        assert levels["mypy/type-error"] == "error" # high

    def test_sarif_skips_non_list_keys(self):
        result = to_sarif(SAMPLE_RESULTS)
        data = json.loads(result)
        rule_ids = [r["ruleId"] for r in data["runs"][0]["results"]]
        # score, summary, is_passing, governance should not appear
        for rid in rule_ids:
            assert "score" not in rid
            assert "summary" not in rid
            assert "is_passing" not in rid

    def test_sarif_empty_results(self):
        result = to_sarif({"score": 100, "is_passing": True, "summary": {}})
        data = json.loads(result)
        assert data["runs"][0]["results"] == []

    def test_sarif_location_fields(self):
        result = to_sarif(SAMPLE_RESULTS)
        data = json.loads(result)
        loc = data["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
        assert loc["artifactLocation"]["uri"] == "test.py"
        assert loc["region"]["startLine"] == 10
        assert loc["region"]["startColumn"] == 5


class TestJunitFormatter:
    def test_valid_xml_output(self):
        result = to_junit(SAMPLE_RESULTS)
        assert result.startswith('<?xml version="1.0"')
        assert "<testsuites" in result
        assert "</testsuites>" in result

    def test_junit_adapter_count(self):
        result = to_junit(SAMPLE_RESULTS)
        assert 'name="ruff"' in result
        assert 'name="mypy"' in result

    def test_junit_failure_count(self):
        result = to_junit(SAMPLE_RESULTS)
        # ruff has 2 failures, mypy has 1
        assert 'failures="2"' in result
        assert 'failures="1"' in result

    def test_junit_total_attributes(self):
        result = to_junit(SAMPLE_RESULTS)
        # 2 adapters (ruff, mypy), 3 total failures
        assert 'tests="2"' in result
        assert 'failures="3"' in result

    def test_junit_empty_adapter_passes(self):
        results = {"ruff": [], "score": 100, "is_passing": True, "summary": {}}
        result = to_junit(results)
        assert 'failures="0"' in result
        assert "<testcase" in result
        assert "<failure" not in result

    def test_junit_escapes_special_chars(self):
        results = {
            "ruff": [{"file": "test.py", "line": 1, "code": "E1",
                       "message": 'Use "quotes" & <brackets>', "severity": "medium"}],
            "score": 90, "is_passing": True, "summary": {},
        }
        result = to_junit(results)
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&quot;" in result

    def test_junit_empty_results(self):
        result = to_junit({"score": 100, "is_passing": True, "summary": {}})
        assert 'tests="0"' in result
        assert 'failures="0"' in result
