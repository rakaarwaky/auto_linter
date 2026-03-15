from src.core._taxonomy.models import Severity, LintResult, GovernanceReport

def test_severity_enum():
    assert Severity.LOW.value == "low"
    assert Severity.CRITICAL.value == "critical"

def test_lint_result_creation():
    result = LintResult(
        file="test.py",
        line=10,
        column=5,
        code="E001",
        message="Test error",
        source="test-linter",
        severity=Severity.HIGH
    )
    assert result.file == "test.py"
    assert result.severity == Severity.HIGH

def test_governance_report_add_result():
    report = GovernanceReport()
    
    # Test Medium
    result_med = LintResult("f1.py", 1, 1, "M1", "Msg", "src", Severity.MEDIUM)
    report.add_result(result_med)
    assert report.score == 98.0
    assert len(report.results) == 1
    
    # Test High
    result_high = LintResult("f2.py", 1, 1, "H1", "Msg", "src", Severity.HIGH)
    report.add_result(result_high)
    assert report.score == 88.0
    
    # Test Critical
    result_crit = LintResult("f3.py", 1, 1, "C1", "Msg", "src", Severity.CRITICAL)
    report.add_result(result_crit)
    assert report.score == 38.0
    assert report.is_passing is False

def test_governance_report_score_floor():
    report = GovernanceReport()
    result_crit = LintResult("f3.py", 1, 1, "C1", "Msg", "src", Severity.CRITICAL)
    report.add_result(result_crit)
    report.add_result(result_crit)
    report.add_result(result_crit)
    assert report.score == 0.0

def test_abstract_linter_adapter():
    from src.core._taxonomy.models import ILinterAdapter
    class ConcreteLinter(ILinterAdapter):
        def scan(self, path): return super().scan(path)
        def name(self): return super().name()
    
    linter = ConcreteLinter()
    assert linter.name() is None
    assert linter.scan("path") is None
