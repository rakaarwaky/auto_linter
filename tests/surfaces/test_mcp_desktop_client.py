"""Tests for MCP desktop client."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from surfaces.mcp_desktop_client import _get_client, _execute_with_retry


class TestGetClient:
    def test_get_client_returns_instance(self):
        mock_client = MagicMock()
        with patch("agent.dependency_injection_container.get_container") as mock_gc:
            container = MagicMock()
            container.desktop_commander = mock_client
            mock_gc.return_value = container
            client = _get_client()
        assert client is mock_client

    def test_get_client_caches(self):
        mock_client = MagicMock()
        with patch("agent.dependency_injection_container.get_container") as mock_gc:
            container = MagicMock()
            container.desktop_commander = mock_client
            mock_gc.return_value = container
            c1 = _get_client()
            c2 = _get_client()
        assert c1 is c2 is mock_client


class TestExecuteWithRetry:
    @pytest.mark.asyncio
    async def test_execute_success_first_try(self):
        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(return_value={"result": "ok"})

        result = await _execute_with_retry(
            client=mock_client,
            command=["echo", "hello"],
            working_dir=".",
            timeout=30,
            max_retries=3,
        )
        assert result["result"] == "ok"
        mock_client.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_retries_on_connection_error(self):
        call_count = [0]
        mock_client = AsyncMock()

        async def mock_execute(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("connection refused")
            return {"result": "ok after retry"}

        mock_client.execute_command = mock_execute

        result = await _execute_with_retry(
            client=mock_client,
            command=["echo", "hello"],
            working_dir=".",
            timeout=30,
            max_retries=3,
        )
        assert "ok after retry" in result["result"]

    @pytest.mark.asyncio
    async def test_execute_returns_error_after_max_retries(self):
        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(side_effect=ConnectionError("permanent error"))

        result = await _execute_with_retry(
            client=mock_client,
            command=["echo", "hello"],
            working_dir=".",
            timeout=30,
            max_retries=3,
        )
        assert "error" in result
        assert "3 attempts" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_timeout_error(self):
        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(side_effect=TimeoutError("timeout"))

        result = await _execute_with_retry(
            client=mock_client,
            command=["echo", "hello"],
            working_dir=".",
            timeout=30,
            max_retries=2,
        )
        assert "error" in result
        assert "2 attempts" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_oserror_retried(self):
        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(side_effect=OSError("os error"))

        result = await _execute_with_retry(
            client=mock_client,
            command=["echo", "hello"],
            working_dir=".",
            timeout=30,
            max_retries=2,
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_all_retries_fail(self):
        """Test _execute_with_retry when all retries fail (line 58)."""
        mock_client = AsyncMock()
        mock_client.execute_command = AsyncMock(
            side_effect=ConnectionError("always fails")
        )

        result = await _execute_with_retry(
            client=mock_client,
            command=["echo", "hello"],
            working_dir=".",
            timeout=30,
            max_retries=5,
        )
        assert "error" in result
        assert "5 attempts" in result["error"]
        assert "suggestion" in result
        assert "DesktopCommander" in result["suggestion"]
