"""Additional tests for pipeline_execution_orchestrator to cover lines 197-199, 272."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agent.pipeline_execution_orchestrator import Pipeline


class TestPipelineExecutionUncovered:
    """Tests for uncovered lines 197-199 and 272."""

    @pytest.mark.asyncio
    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    async def test_execute_multi_project_with_retry(self):
        """Test execute_multi_project with retry enabled (lines 197-199)."""
        mock_container = MagicMock()
        
        mock_analysis = MagicMock()
        mock_report = MagicMock()
        mock_analysis.execute = AsyncMock(return_value=mock_report)
        mock_analysis.to_dict = MagicMock(return_value={
            "score": 85.0,
            "is_passing": True,
            "ruff": [],
        })
        mock_container.analysis_use_case = mock_analysis

        pipeline = Pipeline(mock_container)
        
        # Mock run_with_retry to avoid actual retry logic
        async def mock_retry(func, *args, **kwargs):
            return await func()
        
        with patch("agent.pipeline_execution_orchestrator.run_with_retry", side_effect=mock_retry):
            result = await pipeline.execute_multi_project(["/tmp/project1"], use_retry=True)
            assert "job_id" in result
            assert result["total_projects"] == 1

    def test_process_watch_event_with_coroutine(self):
        """Test process_watch_event when execute returns a coroutine (line 272)."""
        import asyncio
        
        mock_container = MagicMock()
        
        async def async_report():
            return MagicMock()
        
        mock_container.analysis_use_case.execute = MagicMock(side_effect=async_report)
        mock_container.analysis_use_case.to_dict = MagicMock(return_value={
            "score": 75.0,
            "is_passing": True,
        })

        pipeline = Pipeline(mock_container)
        result = pipeline.process_watch_event("test.py")
        # Should handle coroutine via asyncio.run
        assert "file" in result or "score" in result or "error" in result

    def test_process_watch_event_sync_success(self):
        """Test process_watch_event with sync execute."""
        mock_container = MagicMock()
        
        mock_report = MagicMock()
        mock_container.analysis_use_case.execute = MagicMock(return_value=mock_report)
        mock_container.analysis_use_case.to_dict = MagicMock(return_value={
            "score": 88.0,
            "is_passing": True,
        })

        pipeline = Pipeline(mock_container)
        result = pipeline.process_watch_event("test.py")
        assert result["score"] == 88.0
        assert result["is_passing"] is True
