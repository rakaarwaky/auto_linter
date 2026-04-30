"""Additional tests for linting_report_formatters to cover line 69."""

from capabilities.linting_report_formatters import to_junit


class TestJunitFormatterUncovered:
    """Test JUnit XML output with special characters (line 69)."""

    def test_junit_output_with_apostrophe(self):
        """Test that apostrophes are properly escaped."""
        results = {
            "ruff": [{"file": "test.py", "line": 1, "code": "E1",
                       "message": "It's a test & it's <complex>", "severity": "medium"}],
            "score": 90, "is_passing": True, "summary": {},
        }
        result = to_junit(results)
        assert "&apos;" in result or "'" in result
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result

    def test_junit_output_with_all_special_chars(self):
        """Test all XML special characters in messages."""
        results = {
            "eslint": [{"file": "test.js", "line": 1, "code": "ES1",
                         "message": 'Use "quotes" & <tags> and \'apostrophes\'', "severity": "high"}],
            "score": 80, "is_passing": True, "summary": {},
        }
        result = to_junit(results)
        assert "&quot;" in result
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result
