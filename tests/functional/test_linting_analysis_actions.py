"""Tests for linting analysis actions."""
import pytest
from unittest.mock import MagicMock
from capabilities.linting_analysis_actions import RunAnalysisUseCase, ApplyFixesUseCase
from taxonomy.lint_result_models import LintResult, Severity, GovernanceReport


class TestRunAnalysisUseCase:
    """Tests for RunAnalysisUseCase."""

    @pytest.fixture
    def mock_adapters(self):
        """Create mock adapters with correct sync API."""
        adapter = MagicMock()
        adapter.name.return_value = "mock"
        adapter.scan.return_value = []
        return [adapter]

    @pytest.fixture
    def use_case(self, mock_adapters):
        """Create RunAnalysisUseCase."""
        return RunAnalysisUseCase(mock_adapters)

    def test_init_stores_adapters(self, use_case, mock_adapters):
        """Init should store adapters."""
        assert use_case.adapters == mock_adapters

    def test_init_stores_tracers(self):
        """Init should store tracers."""
        tracer = MagicMock()
        uc = RunAnalysisUseCase([], tracers={"python": tracer})
        assert uc.tracers == {"python": tracer}

    def test_init_default_tracers(self):
        """Init should default tracers to empty dict."""
        uc = RunAnalysisUseCase([])
        assert uc.tracers == {}

    @pytest.mark.asyncio
    async def test_execute_calls_all_adapters(self, use_case):
        """Execute should call scan on all adapters."""
        await use_case.execute("/test/path")
        for adapter in use_case.adapters:
            adapter.scan.assert_called_once_with("/test/path")

    @pytest.mark.asyncio
    async def test_execute_returns_governance_report(self, use_case):
        """Execute should return a GovernanceReport."""
        result = await use_case.execute("/test/path")
        assert isinstance(result, GovernanceReport)
        assert result.results == []

    @pytest.mark.asyncio
    async def test_execute_collects_results(self):
        """Execute should collect results from adapters."""
        adapter = MagicMock()
        adapter.name.return_value = "ruff"
        lint_result = LintResult(
            file="test.py", line=1, column=0,
            code="E501", message="Line too long", source="ruff"
        )
        adapter.scan.return_value = [lint_result]
        uc = RunAnalysisUseCase([adapter])
        report = await uc.execute("/test/path")
        assert len(report.results) == 1
        assert report.results[0].code == "E501"

    @pytest.mark.asyncio
    async def test_execute_handles_adapter_exception(self, caplog):
        """Execute should handle adapter exceptions gracefully."""
        import logging
        adapter = MagicMock()
        adapter.name.return_value = "failing"
        adapter.scan.side_effect = RuntimeError("boom")
        uc = RunAnalysisUseCase([adapter])
        with caplog.at_level(logging.ERROR):
            report = await uc.execute("/test/path")
        assert len(report.results) == 0
        assert "Error in adapter failing" in caplog.text

    @pytest.mark.asyncio
    async def test_execute_enriches_with_scope(self):
        """Execute should enrich results with enclosing scope."""
        adapter = MagicMock()
        adapter.name.return_value = "ruff"
        lint_result = LintResult(
            file="test.py", line=5, column=0,
            code="E501", message="Line too long", source="ruff"
        )
        adapter.scan.return_value = [lint_result]

        tracer = MagicMock()
        tracer.show_enclosing_scope.return_value = "function test_func"
        uc = RunAnalysisUseCase([adapter], tracers={"python": tracer})
        report = await uc.execute("/test/path")
        assert report.results[0].enclosing_scope == "function test_func"

    @pytest.mark.asyncio
    async def test_execute_enriches_missing_argument_call_chain(self):
        """Execute should trace call chain for missing argument errors."""
        adapter = MagicMock()
        adapter.name.return_value = "mypy"
        lint_result = LintResult(
            file="test.py", line=10, column=0,
            code="mypy", message="Missing argument 'x' for function 'foo'",
            source="mypy"
        )
        adapter.scan.return_value = [lint_result]

        tracer = MagicMock()
        tracer.show_enclosing_scope.return_value = None
        tracer.trace_call_chain.return_value = ["caller1.py:5", "caller2.py:10"]
        uc = RunAnalysisUseCase([adapter], tracers={"python": tracer})
        report = await uc.execute("/test/path")
        assert len(report.results[0].related_locations) == 2
        assert "Caller: caller1.py:5" in report.results[0].related_locations

    @pytest.mark.asyncio
    async def test_execute_enriches_unused_variable_flow(self):
        """Execute should trace data flow for unused variable errors."""
        adapter = MagicMock()
        adapter.name.return_value = "ruff"
        lint_result = LintResult(
            file="test.py", line=3, column=0,
            code="F841", message="Local variable 'x' is assigned to but never used",
            source="ruff"
        )
        adapter.scan.return_value = [lint_result]

        tracer = MagicMock()
        tracer.show_enclosing_scope.return_value = None
        tracer.find_flow.return_value = ["flow1", "flow2"]
        uc = RunAnalysisUseCase([adapter], tracers={"python": tracer})
        report = await uc.execute("/test/path")
        assert report.results[0].related_locations == ["flow1", "flow2"]

    def test_to_dict_empty_report(self, use_case):
        """to_dict should handle empty report."""
        report = GovernanceReport()
        result = use_case.to_dict(report)
        assert isinstance(result, dict)
        assert result["governance"] == []
        assert result["ruff"] == []
        assert result["score"] is not None

    def test_to_dict_with_results(self, use_case):
        """to_dict should serialize results by source."""
        report = GovernanceReport()
        report.add_result(LintResult(
            file="test.py", line=1, column=0,
            code="E501", message="Line too long", source="ruff"
        ))
        report.add_result(LintResult(
            file="test.py", line=2, column=0,
            code="mypy", message="Missing type", source="mypy"
        ))
        result = use_case.to_dict(report)
        assert len(result["ruff"]) == 1
        assert len(result["mypy"]) == 1
        assert result["summary"]["ruff"] == 1
        assert result["summary"]["mypy"] == 1

    def test_to_dict_summary_source_mapped_to_governance(self, use_case):
        """to_dict should map summary source to governance."""
        report = GovernanceReport()
        report.add_result(LintResult(
            file="test.py", line=1, column=0,
            code="SUM", message="Summary", source="summary"
        ))
        result = use_case.to_dict(report)
        assert len(result["governance"]) == 1

    def test_to_dict_includes_score_and_passing(self, use_case):
        """to_dict should include score and is_passing."""
        report = GovernanceReport()
        result = use_case.to_dict(report)
        assert "score" in result
        assert "is_passing" in result


class TestApplyFixesUseCase:
    """Tests for ApplyFixesUseCase."""

    @pytest.fixture
    def mock_adapters(self):
        """Create mock adapters with correct sync API."""
        adapter = MagicMock()
        adapter.name.return_value = "mock"
        adapter.apply_fix.return_value = True
        return [adapter]

    @pytest.fixture
    def use_case(self, mock_adapters):
        """Create ApplyFixesUseCase."""
        return ApplyFixesUseCase(mock_adapters)

    def test_init_stores_adapters(self, use_case, mock_adapters):
        """Init should store adapters."""
        assert use_case.adapters == mock_adapters

    @pytest.mark.asyncio
    async def test_apply_fix_calls_adapters(self, use_case):
        """Apply fixes should call apply_fix on adapters."""
        await use_case.execute("/test/path")
        for adapter in use_case.adapters:
            adapter.apply_fix.assert_called_once_with("/test/path")

    @pytest.mark.asyncio
    async def test_apply_fix_returns_log(self, use_case):
        """Apply fixes should return output log."""
        result = await use_case.execute("/test/path")
        assert "Applied automatic fixes" in result

    @pytest.mark.asyncio
    async def test_apply_fix_skips_governance(self):
        """Apply fixes should skip governance adapter."""
        gov_adapter = MagicMock()
        gov_adapter.name.return_value = "governance"
        other_adapter = MagicMock()
        other_adapter.name.return_value = "ruff"
        other_adapter.apply_fix.return_value = True
        uc = ApplyFixesUseCase([gov_adapter, other_adapter])
        await uc.execute("/test/path")
        gov_adapter.apply_fix.assert_not_called()
        other_adapter.apply_fix.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_fix_returns_false(self):
        """Apply fixes should handle adapter returning False."""
        adapter = MagicMock()
        adapter.name.return_value = "ruff"
        adapter.apply_fix.return_value = False
        uc = ApplyFixesUseCase([adapter])
        result = await uc.execute("/test/path")
        assert "No fixes applied" in result

    @pytest.mark.asyncio
    async def test_apply_fix_handles_exception(self):
        """Apply fixes should handle exceptions."""
        adapter = MagicMock()
        adapter.name.return_value = "ruff"
        adapter.apply_fix.side_effect = RuntimeError("boom")
        uc = ApplyFixesUseCase([adapter])
        result = await uc.execute("/test/path.py")
        assert "Error during fix application" in result

    @pytest.mark.asyncio
    async def test_apply_fix_init_default_tracers(self):
        """Init should default tracers to empty dict."""
        uc = ApplyFixesUseCase([])
        assert uc.tracers == {}

    @pytest.mark.asyncio
    async def test_apply_fix_semantic_rename(self):
        """Apply fixes should perform semantic rename for naming violations."""
        adapter = MagicMock()
        adapter.name.return_value = "ruff"
        lint_result = LintResult(
            file="test.py", line=1, column=0,
            code="N802", message="Function name `MyFunc` should be lowercase",
            source="ruff"
        )
        adapter.scan.return_value = [lint_result]
        adapter.apply_fix.return_value = True

        tracer = MagicMock()
        tracer.get_variant_dict.return_value = {"snake_case": "my_func", "pascal_case": "MyFunc"}
        tracer.project_wide_rename.return_value = 3

        uc = ApplyFixesUseCase([adapter], tracers={"python": tracer})
        result = await uc.execute("test.py")
        assert "Semantic Rename" in result
        assert "MyFunc" in result
        assert "my_func" in result
