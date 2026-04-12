"""Comprehensive tests for agent/pipeline_execution_orchestrator.py — 100% coverage."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agent.pipeline_execution_orchestrator import Pipeline
from agent.tracking_job_registry import create_job, list_jobs


@pytest.fixture
def mock_container():
    container = MagicMock()
    # Default analysis mock
    analysis_report = MagicMock()
    analysis_report.results = []
    analysis_report.score = 100.0
    analysis_report.is_passing = True

    container.analysis_use_case.execute = AsyncMock(return_value=analysis_report)
    container.analysis_use_case.to_dict = MagicMock(return_value={
        "score": 100.0, "is_passing": True, "ruff": [], "mypy": [],
        "governance": [], "summary": {},
    })
    container.fixes_use_case.execute = AsyncMock(return_value="All fixes applied.")
    container.adapters = [MagicMock(name=lambda: "ruff")]
    container.hooks_use_case.install = MagicMock(return_value=True)
    container.hooks_use_case.uninstall = MagicMock(return_value=True)
    return container


class TestPipelineInit:
    def test_init(self, mock_container):
        pipeline = Pipeline(mock_container)
        assert pipeline.container is mock_container


class TestPipelineValidateAction:
    def test_valid_actions(self, mock_container):
        pipeline = Pipeline(mock_container)
        for action in ("check", "scan", "fix", "report", "security",
                       "complexity", "duplicates", "trends",
                       "version", "adapters", "install-hook", "install_hook",
                       "uninstall-hook", "uninstall_hook"):
            assert pipeline._validate_action(action) is True

    def test_invalid_actions(self, mock_container):
        pipeline = Pipeline(mock_container)
        assert not pipeline._validate_action("unknown")
        assert not pipeline._validate_action("")


class TestPipelineErrorResponse:
    def test_error_format(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = pipeline._error_response("Test error", job_id="abc123")
        assert result["error"] == "Test error"
        assert result["job_id"] == "abc123"

    def test_error_with_extra(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = pipeline._error_response("Error", code=500)
        assert result["error"] == "Error"
        assert result["code"] == 500


class TestPipelineExecute:
    @pytest.mark.asyncio
    async def test_execute_invalid_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("unknown_action", {"path": "src/"})
        assert "error" in result
        assert "Invalid action" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_with_retry(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("check", {"path": "src/"}, use_retry=True)
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_execute_exception(self, mock_container):
        mock_container.analysis_use_case.execute = AsyncMock(
            side_effect=RuntimeError("boom")
        )
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("check", {"path": "src/"})
        assert "error" in result


class TestPipelineExecuteCheck:
    @pytest.mark.asyncio
    async def test_execute_check_success(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_check("src/")
        assert "score" in result
        assert "job_id" in result


class TestPipelineDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_check(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("check", {"path": "src/"})
        mock_container.analysis_use_case.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_scan(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("scan", {"path": "src/"})
        assert "score" in result

    @pytest.mark.asyncio
    async def test_dispatch_fix(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("fix", {"path": "src/"})
        assert "output" in result
        mock_container.fixes_use_case.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_security(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("security", {"path": "src/"})
        assert "bandit" in result

    @pytest.mark.asyncio
    async def test_dispatch_complexity(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("complexity", {"path": "src/"})
        assert "radon" in result

    @pytest.mark.asyncio
    async def test_dispatch_duplicates(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("duplicates", {"path": "src/"})
        assert "duplicates" in result

    @pytest.mark.asyncio
    async def test_dispatch_trends(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("trends", {"path": "src/"})
        assert "trends" in result

    @pytest.mark.asyncio
    async def test_dispatch_report_text(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("report", {"path": "src/", "format": "text"})
        assert "format" in result

    @pytest.mark.asyncio
    async def test_dispatch_report_json(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("report", {"path": "src/", "format": "json"})
        assert result["format"] == "json"

    @pytest.mark.asyncio
    async def test_dispatch_report_sarif(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("report", {"path": "src/", "format": "sarif"})
        assert result["format"] == "sarif"

    @pytest.mark.asyncio
    async def test_dispatch_report_junit(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("report", {"path": "src/", "format": "junit"})
        assert result["format"] == "junit"

    @pytest.mark.asyncio
    async def test_dispatch_report_default_format(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("report", {"path": "src/"})
        assert result["format"] == "text"

    @pytest.mark.asyncio
    async def test_execute_check_exception(self, mock_container):
        mock_container.analysis_use_case.execute = AsyncMock(
            side_effect=RuntimeError("analysis failed")
        )
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_check("src/")
        assert "error" in result
        assert result["error"] == "analysis failed"
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_dispatch_version(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("version", {})
        assert "version" in result

    @pytest.mark.asyncio
    async def test_dispatch_version_not_found(self, mock_container):
        """Test fallback when package metadata is not found."""
        import importlib.metadata
        pipeline = Pipeline(mock_container)
        orig_version = importlib.metadata.version
        try:
            importlib.metadata.version = MagicMock(
                side_effect=importlib.metadata.PackageNotFoundError("not found")
            )
            result = await pipeline._dispatch("version", {})
            assert result["version"] == "1.0.0"
        finally:
            importlib.metadata.version = orig_version

    @pytest.mark.asyncio
    async def test_dispatch_adapters(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("adapters", {})
        assert "adapters" in result
        assert isinstance(result["adapters"], list)

    @pytest.mark.asyncio
    async def test_dispatch_install_hook(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("install-hook", {})
        assert "installed" in result

    @pytest.mark.asyncio
    async def test_dispatch_install_hook_underscore(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("install_hook", {})
        assert "installed" in result

    @pytest.mark.asyncio
    async def test_dispatch_uninstall_hook(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("uninstall-hook", {})
        assert "uninstalled" in result

    @pytest.mark.asyncio
    async def test_dispatch_uninstall_hook_underscore(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("uninstall_hook", {})
        assert "uninstalled" in result

    @pytest.mark.asyncio
    async def test_dispatch_unknown_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("unknown_action", {})
        assert "error" in result
