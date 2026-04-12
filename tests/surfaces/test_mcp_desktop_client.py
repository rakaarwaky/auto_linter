"""Tests for MCP desktop client module."""

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from surfaces.mcp_desktop_client import (
    _get_client,
    _execute_with_retry,
    _running_jobs,
    DESKTOP_COMMANDER_URL,
)


class TestGetClient:
    def test_get_client_returns_adapter(self):
        """Test _get_client returns DesktopCommanderAdapter."""
        from infrastructure.desktop_commander_adapter import DesktopCommanderAdapter
        # Reset the singleton first
        import surfaces.mcp_desktop_client as client_module
        client_module._desktop_commander_client = None

        client = _get_client()
        assert client is not None
        assert isinstance(client, DesktopCommanderAdapter)

    def test_get_client_singleton(self):
        """Test _get_client returns same instance on repeated calls."""
        import surfaces.mcp_desktop_client as client_module
        client_module._desktop_commander_client = None

        client1 = _get_client()
        client2 = _get_client()
        assert client1 is client2


class TestExecuteWithRetry:
    @pytest.mark.asyncio
    async def test_execute_success_first_try(self):
        """Test execute succeeds on first try."""
        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(return_value={
            "stdout": "output", "stderr": "", "exit_code": 0
        })

        result = await _execute_with_retry(
            client=mock_client,
            command=["echo", "test"],
            working_dir="/tmp",
            timeout=30
        )
        assert "stdout" in result
        mock_client.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_retry_then_success(self):
        """Test execute retries then succeeds."""
        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(
            side_effect=[
                ConnectionError("Connection refused"),
                {"stdout": "output", "stderr": "", "exit_code": 0}
            ]
        )

        result = await _execute_with_retry(
            client=mock_client,
            command=["echo", "test"],
            working_dir="/tmp",
            timeout=30,
            max_retries=3
        )
        assert "stdout" in result
        assert mock_client.execute_command.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_all_retries_fail(self):
        """Test execute fails after all retries."""
        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(
            side_effect=ConnectionError("Connection refused")
        )

        result = await _execute_with_retry(
            client=mock_client,
            command=["echo", "test"],
            working_dir="/tmp",
            timeout=30,
            max_retries=3
        )
        assert "error" in result
        assert "unavailable" in result["error"].lower()
        assert mock_client.execute_command.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_timeout_error(self):
        """Test execute handles TimeoutError."""
        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(
            side_effect=TimeoutError("Command timed out")
        )

        result = await _execute_with_retry(
            client=mock_client,
            command=["sleep", "100"],
            working_dir="/tmp",
            timeout=30,
            max_retries=2
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_os_error(self):
        """Test execute handles OSError."""
        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(
            side_effect=OSError("OS error")
        )

        result = await _execute_with_retry(
            client=mock_client,
            command=["test"],
            working_dir="/tmp",
            timeout=30,
            max_retries=2
        )
        assert "error" in result


class TestRunningJobs:
    def test_running_jobs_is_dict(self):
        """Test _running_jobs is a dictionary."""
        assert isinstance(_running_jobs, dict)

    def test_running_jobs_can_be_modified(self):
        """Test _running_jobs can be modified."""
        _running_jobs["test_job"] = {"status": "running"}
        assert "test_job" in _running_jobs
        del _running_jobs["test_job"]


class TestDesktopCommanderUrl:
    def test_default_url(self):
        """Test default DESKTOP_COMMANDER_URL."""
        assert isinstance(DESKTOP_COMMANDER_URL, str)
