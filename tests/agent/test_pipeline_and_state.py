"""Agent layer integration tests - Pipeline and State Manager."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from agent.pipeline_execution_orchestrator import Pipeline
from agent.lifecycle_state_manager import AgentState, get_state, _state
from agent.tracking_job_registry import create_job, get_job, complete_job, fail_job


# Reset global state before each test
@pytest.fixture(autouse=True)
def reset_state():
    global _state
    _state._status = "initializing"
    _state.started = False
    _state.start_time = None
    yield
    _state._status = "initializing"
    _state.started = False
    _state.start_time = None


class TestPipelineExecutionOrchestrator:
    """Test pipeline execution orchestrator."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.adapters = []
        container.analysis_use_case = MagicMock()
        container.analysis_use_case.execute = AsyncMock(return_value=MagicMock())
        container.analysis_use_case.to_dict = MagicMock(return_value={"score": 100})
        container.fixes_use_case = MagicMock()
        container.fixes_use_case.execute = AsyncMock(return_value="Fixed")
        container.hooks_use_case = MagicMock()
        container.hooks_use_case.install = MagicMock(return_value=True)
        container.hooks_use_case.uninstall = MagicMock(return_value=True)
        return container

    @pytest.mark.asyncio
    async def test_pipeline_init(self, mock_container):
        """Pipeline initializes with container."""
        pipeline = Pipeline(mock_container)
        assert pipeline.container == mock_container

    @pytest.mark.asyncio
    async def test_execute_check_returns_dict(self, mock_container):
        """execute_check returns results dict."""
        # Setup mock
        report = MagicMock()
        report.score = 100
        mock_container.analysis_use_case.execute = AsyncMock(return_value=report)
        mock_container.analysis_use_case.to_dict = MagicMock(return_value={"score": 100})
        
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_check("src/")
        
        assert "score" in result
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_execute_check_handles_error(self, mock_container):
        """execute_check handles errors gracefully."""
        mock_container.analysis_use_case.execute = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        pipeline = Pipeline(mock_container)
        result = await pipeline.execute_check("src/")
        
        assert "error" in result
        assert "job_id" in result

    @pytest.mark.asyncio
    async def test_dispatch_check_action(self, mock_container):
        """Pipeline dispatches check action."""
        report = MagicMock()
        mock_container.analysis_use_case.execute = AsyncMock(return_value=report)
        mock_container.analysis_use_case.to_dict = MagicMock(return_value={"score": 100})
        
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("check", {"path": "src/"})
        
        assert "score" in result

    @pytest.mark.asyncio
    async def test_dispatch_fix_action(self, mock_container):
        """Pipeline dispatches fix action."""
        mock_container.fixes_use_case.execute = AsyncMock(return_value="Fixed 3 files")
        
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("fix", {"path": "src/"})
        
        assert "output" in result

    @pytest.mark.asyncio
    async def test_dispatch_security_action(self, mock_container):
        """Pipeline dispatches security action."""
        report = MagicMock()
        mock_container.analysis_use_case.execute = AsyncMock(return_value=report)
        mock_container.analysis_use_case.to_dict = MagicMock(
            return_value={"bandit": [{"code": "B001"}]}
        )
        
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("security", {"path": "src/"})
        
        assert "bandit" in result

    @pytest.mark.asyncio
    async def test_dispatch_version_action(self, mock_container):
        """Pipeline returns version."""
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("version", {})
        
        assert "version" in result

    @pytest.mark.asyncio
    async def test_dispatch_adapters_action(self, mock_container):
        """Pipeline returns adapter list."""
        mock_container.adapters = [MagicMock(name=lambda: "ruff")]
        
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("adapters", {})
        
        assert "adapters" in result

    @pytest.mark.asyncio
    async def test_dispatch_unknown_action(self, mock_container):
        """Unknown action returns error."""
        pipeline = Pipeline(mock_container)
        result = await pipeline._dispatch("unknown_action", {})
        
        assert "error" in result

    def test_validate_action_valid(self, mock_container):
        """Valid actions pass validation."""
        pipeline = Pipeline(mock_container)

        assert pipeline._validate_action("check")
        assert pipeline._validate_action("fix")
        assert pipeline._validate_action("version")

    def test_validate_action_invalid(self, mock_container):
        """Invalid actions fail validation."""
        pipeline = Pipeline(mock_container)

        assert not pipeline._validate_action("invalid")
        assert not pipeline._validate_action("random")

    def test_error_response_format(self, mock_container):
        """Error response has correct format."""
        pipeline = Pipeline(mock_container)
        response = pipeline._error_response("Test error", job_id="123")
        
        assert response["error"] == "Test error"
        assert response["job_id"] == "123"


class TestAgentLifecycleState:
    """Test agent lifecycle state manager."""

    def test_agent_state_init(self):
        """Initial state is initializing."""
        state = AgentState()
        
        assert state.status == "initializing"
        assert not state.started
        assert state.uptime == 0

    def test_mark_started(self):
        """mark_started transitions to running."""
        state = AgentState()
        state.mark_started()

        assert state.status == "running"
        assert state.started
        assert state.start_time is not None

    def test_mark_stopped(self):
        """mark_stopped transitions to stopped."""
        state = AgentState()
        state.mark_started()  # Start first
        state.mark_stopped()
        
        assert state.status == "stopped"

    def test_mark_degraded(self):
        """mark_degraded transitions to degraded."""
        state = AgentState()
        state.mark_started()
        state.mark_degraded()
        
        assert state.status == "degraded"

    def test_uptime_tracking(self):
        """uptime is tracked."""
        state = AgentState()
        state.mark_started()
        
        # Should have some small uptime
        assert state.uptime >= 0

    def test_health_report(self):
        """health returns full report."""
        state = AgentState()
        health = state.health()
        
        assert "status" in health
        assert "uptime_seconds" in health
        assert "started" in health


class TestTrackingJobRegistry:
    """Test job tracking registry."""

    def test_create_job(self):
        """Create job returns ID."""
        job_id = create_job("check")
        
        assert job_id is not None
        assert isinstance(job_id, str)

    def test_get_job(self):
        """Get job returns job info."""
        job_id = create_job("check")
        job = get_job(job_id)
        
        assert job is not None

    def test_complete_job(self):
        """Complete job updates status."""
        job_id = create_job("check")
        complete_job(job_id, {"result": "ok"})
        
        job = get_job(job_id)
        assert job["status"] == "completed"

    def test_fail_job(self):
        """Fail job updates status."""
        job_id = create_job("check")
        fail_job(job_id, "Error")
        
        job = get_job(job_id)
        assert job["status"] == "failed"


class TestGetStateFunction:
    """Test get_state function."""

    def test_get_state_returns_singleton(self):
        """get_state returns the singleton."""
        state = get_state()
        
        assert isinstance(state, AgentState)

    def test_get_state_returns_same_instance(self):
        """Multiple calls return same instance."""
        s1 = get_state()
        s2 = get_state()
        
        assert s1 is s2