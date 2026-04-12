"""Comprehensive tests for agent/lifecycle_state_manager.py — 100% coverage."""

import pytest
from agent.lifecycle_state_manager import AgentState, get_state


class TestAgentState:
    def test_init(self):
        state = AgentState()
        assert state.started is False
        assert state.status == "initializing"
        assert state.uptime == 0
        assert state.start_time is None

    def test_mark_started(self):
        state = AgentState()
        state.mark_started()
        assert state.started is True
        assert state.status == "running"
        assert state.uptime > 0
        assert state.start_time is not None

    def test_mark_stopped(self):
        state = AgentState()
        state.mark_started()
        state.mark_stopped()
        assert state.status == "stopped"
        assert state.started is True

    def test_mark_degraded(self):
        state = AgentState()
        state.mark_started()
        state.mark_degraded()
        assert state.status == "degraded"
        assert state.started is True

    def test_uptime_before_start(self):
        state = AgentState()
        assert state.uptime == 0

    def test_uptime_after_start(self):
        state = AgentState()
        state.mark_started()
        import time
        time.sleep(0.01)
        assert state.uptime > 0

    def test_health_initial(self):
        state = AgentState()
        health = state.health()
        assert health["status"] == "initializing"
        assert health["uptime_seconds"] == 0
        assert health["started"] is False

    def test_health_running(self):
        state = AgentState()
        state.mark_started()
        health = state.health()
        assert health["status"] == "running"
        assert health["uptime_seconds"] >= 0
        assert health["started"] is True


class TestGetState:
    def test_returns_singleton(self):
        s1 = get_state()
        s2 = get_state()
        assert s1 is s2

    def test_returns_agent_state(self):
        state = get_state()
        assert isinstance(state, AgentState)
