"""Comprehensive tests for infrastructure/stdio_transport_client.py — 100% coverage."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from infrastructure.stdio_transport_client import StdioClient


class TestStdioClient:
    @pytest.mark.asyncio
    async def test_execute_success(self):
        client = StdioClient()
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"stdout\n", b""))
        mock_proc.returncode = 0

        with patch("infrastructure.stdio_transport_client.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            result = await client.execute(["echo", "hello"], ".")
            assert result["stdout"] == "stdout\n"
            assert result["returncode"] == 0

    @pytest.mark.asyncio
    async def test_execute_with_stderr(self):
        client = StdioClient()
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b"stderr\n"))
        mock_proc.returncode = 1

        with patch("infrastructure.stdio_transport_client.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            result = await client.execute(["invalid_cmd"], ".")
            assert result["stderr"] == "stderr\n"
            assert result["returncode"] == 1

    @pytest.mark.asyncio
    async def test_execute_exception(self):
        client = StdioClient()

        with patch("infrastructure.stdio_transport_client.asyncio.create_subprocess_exec",
                   side_effect=OSError("No such file")):
            result = await client.execute(["nonexistent"], ".")
            assert "error" in result

    @pytest.mark.asyncio
    async def test_health_check(self):
        client = StdioClient()
        result = await client.health_check()
        assert result["status"] == "healthy"
        assert result["protocol"] == "Stdio"

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        client = StdioClient(timeout=0.001)

        mock_proc = AsyncMock()
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()

        async def slow_communicate():
            await asyncio.sleep(10)
            return (b"", b"")

        mock_proc.communicate = slow_communicate

        with patch("infrastructure.stdio_transport_client.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            result = await client.execute(["slow"], ".")
            assert "error" in result
            assert result["returncode"] == -1

    @pytest.mark.asyncio
    async def test_execute_cwd(self):
        client = StdioClient()
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"ok\n", b""))
        mock_proc.returncode = 0

        with patch("infrastructure.stdio_transport_client.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            result = await client.execute(["pwd"], "/tmp")
            assert result["returncode"] == 0

    @pytest.mark.asyncio
    async def test_execute_decode_error(self):
        client = StdioClient()
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"\xff\xfe", b""))
        mock_proc.returncode = 0

        with patch("infrastructure.stdio_transport_client.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            result = await client.execute(["cmd"], ".")
            # Should handle decode error gracefully
            assert "returncode" in result or "error" in result

    @pytest.mark.asyncio
    async def test_execute_file_not_found(self):
        client = StdioClient()
        
        with patch("infrastructure.stdio_transport_client.asyncio.create_subprocess_exec",
                   side_effect=FileNotFoundError("cmd not found")):
            result = await client.execute(["nonexistent"], ".")
            assert "error" in result
            assert result["returncode"] == 127

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        client = StdioClient()
        
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b"error"))
        mock_proc.returncode = 1

        with patch("infrastructure.stdio_transport_client.asyncio.create_subprocess_exec",
                   return_value=mock_proc):
            result = await client.health_check()
            assert result["status"] == "unhealthy"

    def test_close(self):
        client = StdioClient()
        # Should not raise
        client.close()
