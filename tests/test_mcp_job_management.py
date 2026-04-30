"""Tests for MCP job management tools (check_status only)."""

import json
import pytest
from unittest.mock import MagicMock, patch
from surfaces.mcp_job_management import register_check_status


class TestCheckStatus:
    def test_register_check_status(self):
        """Test check_status tool is registered."""
        mcp = MagicMock()
        register_check_status(mcp)
        mcp.tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_status_no_jobs(self):
        """Test check_status with no jobs."""
        with patch("agent.tracking_job_registry._jobs", {}):
            mcp = MagicMock()
            tool_func = None

            def capture_tool(func=None):
                nonlocal tool_func
                def decorator(f):
                    nonlocal tool_func
                    tool_func = f
                    return f
                if func is None:
                    return decorator
                return decorator(func)
            mcp.tool.side_effect = capture_tool

            register_check_status(mcp)
            result = await tool_func()
            data = json.loads(result)
            assert data["total"] == 0
            assert data["jobs"] == []

    @pytest.mark.asyncio
    async def test_check_status_all_jobs(self):
        """Test check_status listing all jobs."""
        mock_jobs = {
            "job-1": {
                "status": "running",
                "action": "lint",
                "started_at": "2024-01-01T00:00:00"
            },
            "job-2": {
                "status": "completed",
                "action": "fix",
                "started_at": "2024-01-01T00:00:00",
                "completed_at": "2024-01-01T00:01:00"
            }
        }
        with patch("agent.tracking_job_registry._jobs", mock_jobs):
            mcp = MagicMock()
            tool_func = None

            def capture_tool(func=None):
                nonlocal tool_func
                def decorator(f):
                    nonlocal tool_func
                    tool_func = f
                    return f
                if func is None:
                    return decorator
                return decorator(func)
            mcp.tool.side_effect = capture_tool

            register_check_status(mcp)
            result = await tool_func()
            data = json.loads(result)
            assert data["total"] == 2
            assert len(data["jobs"]) == 2

    @pytest.mark.asyncio
    async def test_check_status_specific_job_exists(self):
        """Test check_status with a specific job_id that exists."""
        mock_jobs = {
            "job-123": {
                "status": "running",
                "action": "lint",
                "started_at": "2024-01-01T00:00:00",
                "completed_at": None,
                "result": None
            }
        }
        with patch("agent.tracking_job_registry._jobs", mock_jobs):
            mcp = MagicMock()
            tool_func = None

            def capture_tool(func=None):
                nonlocal tool_func
                def decorator(f):
                    nonlocal tool_func
                    tool_func = f
                    return f
                if func is None:
                    return decorator
                return decorator(func)
            mcp.tool.side_effect = capture_tool

            register_check_status(mcp)
            result = await tool_func(job_id="job-123")
            data = json.loads(result)
            assert data["job_id"] == "job-123"
            assert data["status"] == "running"
            assert data["action"] == "lint"

    @pytest.mark.asyncio
    async def test_check_status_specific_job_not_found(self):
        """Test check_status with a specific job_id that doesn't exist."""
        with patch("agent.tracking_job_registry._jobs", {}):
            mcp = MagicMock()
            tool_func = None

            def capture_tool(func=None):
                nonlocal tool_func
                def decorator(f):
                    nonlocal tool_func
                    tool_func = f
                    return f
                if func is None:
                    return decorator
                return decorator(func)
            mcp.tool.side_effect = capture_tool

            register_check_status(mcp)
            result = await tool_func(job_id="nonexistent")
            data = json.loads(result)
            assert "error" in data
            assert "not found" in data["error"]
            assert data["status"] == "not_found"
