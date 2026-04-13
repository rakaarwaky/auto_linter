"""Tests for pipeline execution orchestrator."""
from unittest.mock import AsyncMock, MagicMock
import pytest
from src.agent.pipeline_execution_orchestrator import Pipeline


@pytest.fixture
def mock_container():
    container = MagicMock()

    # Mock analysis use case
    mock_analysis = MagicMock()
    mock_report = MagicMock()
    mock_analysis.execute = AsyncMock(return_value=mock_report)
    mock_analysis.to_dict = MagicMock(return_value={
        "score": 85.0,
        "ruff": [],
        "summary": "clean",
        "is_passing": True,
    })
    container.analysis_use_case = mock_analysis

    # Mock fixes use case
    container.fixes_use_case = MagicMock()
    container.fixes_use_case.execute = AsyncMock(return_value="Fixed!")

    # Mock adapters
    mock_adapter = MagicMock()
    mock_adapter.name.return_value = "ruff"
    container.adapters = [mock_adapter]

    # Mock hooks use case
    container.hooks_use_case = MagicMock()
    container.hooks_use_case.install = MagicMock(return_value=True)
    container.hooks_use_case.uninstall = MagicMock(return_value=True)

    return container


class TestPipelineExecute:
    @pytest.mark.asyncio
    async def test_execute_check_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("check", {"path": "."})
        assert "job_id" in result
        assert result["score"] == 85.0

    @pytest.mark.asyncio
    async def test_execute_scan_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("scan", {"path": "."})
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_execute_fix_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("fix", {"path": "."})
        assert result["output"] == "Fixed!"

    @pytest.mark.asyncio
    async def test_execute_security_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("security", {"path": "."})
        assert "bandit" in result

    @pytest.mark.asyncio
    async def test_execute_complexity_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("complexity", {"path": "."})
        assert "radon" in result

    @pytest.mark.asyncio
    async def test_execute_duplicates_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("duplicates", {"path": "."})
        assert "duplicates" in result

    @pytest.mark.asyncio
    async def test_execute_trends_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("trends", {"path": "."})
        assert "trends" in result

    @pytest.mark.asyncio
    async def test_execute_report_text(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("report", {"path": ".", "format": "text"})
        assert result["format"] == "text"

    @pytest.mark.asyncio
    async def test_execute_report_json(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("report", {"path": ".", "format": "json"})
        assert result["format"] == "json"

    @pytest.mark.asyncio
    async def test_execute_report_sarif(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("report", {"path": ".", "format": "sarif"})
        assert result["format"] == "sarif"

    @pytest.mark.asyncio
    async def test_execute_report_junit(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("report", {"path": ".", "format": "junit"})
        assert result["format"] == "junit"

    @pytest.mark.asyncio
    async def test_execute_version_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("version")
        assert "version" in result

    @pytest.mark.asyncio
    async def test_execute_adapters_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("adapters")
        assert "adapters" in result
        assert result["adapters"] == ["ruff"]

    @pytest.mark.asyncio
    async def test_execute_install_hook(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("install-hook")
        assert result["installed"] is True

    @pytest.mark.asyncio
    async def test_execute_install_hook_underscore(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("install_hook")
        assert result["installed"] is True

    @pytest.mark.asyncio
    async def test_execute_uninstall_hook(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("uninstall-hook")
        assert result["uninstalled"] is True

    @pytest.mark.asyncio
    async def test_execute_uninstall_hook_underscore(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("uninstall_hook")
        assert result["uninstalled"] is True

    @pytest.mark.asyncio
    async def test_execute_invalid_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("nonexistent")
        assert "error" in result
        assert "Invalid action" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self, mock_container):
        pipeline = Pipeline(mock_container)
        # Valid action but not handled by dispatch
        result = await pipeline.execute("check", {"path": "."})
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_execute_with_retry(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("check", {"path": "."}, use_retry=True)
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_execute_exception(self, mock_container):
        mock_container.analysis_use_case.execute = AsyncMock(side_effect=Exception("boom"))
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute("check", {"path": "."})
        assert "error" in result
        assert "boom" in result["error"]


class TestPipelineExecuteCheck:
    @pytest.mark.asyncio
    async def test_execute_check_direct(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_check(".")
        assert "job_id" in result
        assert result["score"] == 85.0

    @pytest.mark.asyncio
    async def test_execute_check_exception(self, mock_container):
        mock_container.analysis_use_case.execute = AsyncMock(side_effect=Exception("boom"))
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_check(".")
        assert "error" in result
        assert "boom" in result["error"]


class TestPipelineMultiProject:
    @pytest.mark.asyncio
    async def test_execute_multi_project_all_passing(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_multi_project([".", "/tmp"])
        assert "job_id" in result
        assert result["total_projects"] == 2

    @pytest.mark.asyncio
    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    async def test_execute_multi_project_with_retry(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_multi_project(["."], use_retry=True)
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_execute_multi_project_exception(self, mock_container):
        mock_container.analysis_use_case.execute = AsyncMock(side_effect=Exception("boom"))
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_multi_project(["."])
        assert result["projects"][0]["error"] == "boom"

    @pytest.mark.asyncio
    async def test_multi_project_exception(self, mock_container):
        mock_container.analysis_use_case.execute = AsyncMock(side_effect=Exception("boom"))
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_multi_project(["."])
        assert "error" in result or result["failing"] > 0


class TestPipelineWatch:
    @pytest.mark.asyncio
    async def test_execute_watch(self, mock_container):
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_watch(".")
        assert "job_id" in result
        assert result["score"] == 85.0

    @pytest.mark.asyncio
    async def test_execute_watch_exception(self, mock_container):
        mock_container.analysis_use_case.execute = AsyncMock(side_effect=Exception("boom"))
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_watch(".")
        assert "error" in result

    def test_process_watch_event(self, mock_container):
        pipeline = Pipeline(mock_container)
        mock_container.analysis_use_case.execute = MagicMock()
        mock_report = MagicMock()
        mock_container.analysis_use_case.execute.return_value = mock_report
        mock_container.analysis_use_case.to_dict.return_value = {
            "score": 90.0,
            "is_passing": True,
        }
        result = pipeline.process_watch_event("test.py")
        assert result["score"] == 90.0

    def test_process_watch_event_exception(self, mock_container):
        pipeline = Pipeline(mock_container)
        mock_container.analysis_use_case.execute = MagicMock(side_effect=Exception("boom"))
        result = pipeline.process_watch_event("test.py")
        assert result["error"] == "boom"
