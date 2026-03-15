import json
import pytest
from unittest.mock import MagicMock, patch
from src.core._taxonomy.models import LintResult, Severity, GovernanceReport
from src.core.capabilities.linting.actions import RunAnalysisUseCase, ApplyFixesUseCase

@pytest.mark.asyncio
async def test_run_analysis_use_case_execute():
    # Setup
    mock_adapter = MagicMock()
    mock_adapter.name.return_value = "mock"
    mock_adapter.scan.return_value = [
        LintResult("file.py", 1, 1, "E1", "Msg", "mock", Severity.MEDIUM)
    ]
    
    use_case = RunAnalysisUseCase(adapters=[mock_adapter])
    
    # Execute
    report = await use_case.execute("path/to/scan")
    
    # Assert
    assert len(report.results) == 1
    assert report.results[0].code == "E1"
    mock_adapter.scan.assert_called_once_with("path/to/scan")

@pytest.mark.asyncio
async def test_run_analysis_use_case_adapter_exception():
    # Setup
    mock_adapter = MagicMock()
    mock_adapter.name.return_value = "fail_mock"
    mock_adapter.scan.side_effect = Exception("error")
    
    use_case = RunAnalysisUseCase(adapters=[mock_adapter])
    
    # Execute (should not raise exception)
    report = await use_case.execute("path/to/scan")
    
    # Assert
    assert len(report.results) == 0

@pytest.mark.asyncio
async def test_run_analysis_use_case_enrichment():
    # Setup
    mock_adapter = MagicMock()
    mock_adapter.name.return_value = "mock"
    mock_adapter.scan.return_value = [
        LintResult("file.py", 10, 1, "E1", "missing argument for function 'test_func'", "mock", Severity.MEDIUM),
        LintResult("file.py", 20, 1, "E2", "unused variable 'x'", "mock", Severity.MEDIUM)
    ]
    
    mock_tracer = MagicMock()
    mock_tracer.show_enclosing_scope.return_value = "def outer"
    mock_tracer.trace_call_chain.return_value = ["caller.py:5"]
    mock_tracer.find_flow.return_value = ["Line 1 [Assignment]: x = 1"]
    
    use_case = RunAnalysisUseCase(adapters=[mock_adapter], tracers={"python": mock_tracer})
    
    # Execute
    report = await use_case.execute("/root/file.py")
    
    # Assert enrichment
    assert report.results[0].enclosing_scope == "def outer"
    assert "Caller: caller.py:5" in report.results[0].related_locations
    assert "Line 1 [Assignment]: x = 1" in report.results[1].related_locations

def test_run_analysis_use_case_to_dict():
    use_case = RunAnalysisUseCase(adapters=[])
    report = GovernanceReport()
    report.add_result(LintResult("file.py", 1, 1, "E1", "Msg", "ruff", Severity.MEDIUM))
    report.add_result(LintResult("sum.py", 2, 2, "S1", "Summary Msg", "summary", Severity.INFO))
    
    output = use_case.to_dict(report)
    
    assert output["score"] == 98.0
    assert len(output["ruff"]) == 1
    assert len(output["governance"]) == 1 # "summary" maps to "governance"
    assert output["summary"]["ruff"] == 1
    assert output["summary"]["governance"] == 1

def test_run_analysis_use_case_to_dict_unknown_source():
    use_case = RunAnalysisUseCase(adapters=[])
    report = GovernanceReport()
    report.add_result(LintResult("file.py", 1, 1, "U1", "Msg", "unknown_tool", Severity.MEDIUM))
    
    output = use_case.to_dict(report)
    
    assert "unknown_tool" in output
    assert len(output["unknown_tool"]) == 1
    assert output["summary"]["unknown_tool"] == 1

@pytest.mark.asyncio
async def test_apply_fixes_use_case_python():
    use_case = ApplyFixesUseCase(venv_bin="/fake/bin")
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="done", stderr="", check_returncode=lambda: None)
        
        result = await use_case.execute("test.py")
        
        assert "Ruff Fix Output" in result
        assert "done" in result
        mock_run.assert_called()

@pytest.mark.asyncio
async def test_apply_fixes_use_case_semantic_rename():
    use_case = ApplyFixesUseCase(venv_bin="/fake/bin")
    mock_tracer = MagicMock()
    mock_tracer.get_variant_dict.return_value = {"snake_case": "good_name", "pascal_case": "GoodName"}
    mock_tracer.project_wide_rename.return_value = 1
    
    use_case.tracers = {"python": mock_tracer}
    
    with patch("subprocess.run") as mock_run:
        # Mock ruff check output with N802 violation
        mock_run.return_value = MagicMock(
            stdout=json.dumps([{"code": "N802", "message": "invalid name 'badName'", "path": "file.py", "line": 1}]), 
            stderr="", 
            check_returncode=lambda: None
        )
        
        result = await use_case.execute("test.py")
        
        assert "Semantic Rename" in result
        assert "Changed 'badName' -> 'good_name'" in result
        mock_tracer.project_wide_rename.assert_called()

@pytest.mark.asyncio
async def test_apply_fixes_use_case_javascript():
    use_case = ApplyFixesUseCase(venv_bin="/fake/bin")
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="fixed", stderr="", check_returncode=lambda: None)
        
        result = await use_case.execute("test.js")
        
        assert "ESLint Fix Output" in result
        assert "Prettier Fix Output" in result
        # Should call ruff (json format), ruff (fix), eslint, and prettier
        assert mock_run.call_count == 4

@pytest.mark.asyncio
async def test_apply_fixes_use_case_file_not_found():
    use_case = ApplyFixesUseCase(venv_bin="/fake/bin")
    
    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = await use_case.execute("test.py")
        assert "Error: Linter executable not found." in result

@pytest.mark.asyncio
async def test_apply_fixes_use_case_semantic_rename_n801():
    use_case = ApplyFixesUseCase(venv_bin="/fake/bin")
    mock_tracer = MagicMock()
    mock_tracer.get_variant_dict.return_value = {"snake_case": "good_name", "pascal_case": "GoodName"}
    mock_tracer.project_wide_rename.return_value = 1
    
    use_case.tracers = {"python": mock_tracer}
    
    with patch("subprocess.run") as mock_run:
        # Mock ruff check output with N801 violation
        mock_run.return_value = MagicMock(
            stdout=json.dumps([{"code": "N801", "message": "class name 'badname' should use CapWords", "path": "file.py", "line": 1}]), 
            stderr="", 
            check_returncode=lambda: None
        )
        
        result = await use_case.execute("test.py")
        
        assert "Semantic Rename" in result
        assert "Changed 'badname' -> 'GoodName'" in result
        mock_tracer.project_wide_rename.assert_called()
