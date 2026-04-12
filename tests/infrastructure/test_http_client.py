"""Tests for HTTP request client."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from infrastructure.http_request_client import HTTPClient


class TestHTTPClient:
    @pytest.mark.asyncio
    async def test_client_init(self):
        """Test HTTPClient initialization."""
        client = HTTPClient("http://localhost:8080/execute")
        assert client.url == "http://localhost:8080/execute"
        assert client.timeout == 300.0

    @pytest.mark.asyncio
    async def test_client_custom_timeout(self):
        """Test HTTPClient with custom timeout."""
        client = HTTPClient("http://localhost:8080/execute", timeout=60.0)
        assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_ensure_client(self):
        """Test _ensure_client creates client."""
        client = HTTPClient("http://localhost:8080/execute")
        result = await client._ensure_client()
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test execute handles timeout."""
        client = HTTPClient("http://localhost:8080/execute", timeout=1.0)
        with patch.object(client, '_ensure_client') as ec:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Timeout")
            ec.return_value = mock_client
            result = await client.execute(["echo"], ".")
            assert "error" in result or "returncode" in result

    @pytest.mark.asyncio
    async def test_close(self):
        """Test close method."""
        client = HTTPClient("http://localhost:8080/execute")
        mock_client = MagicMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        client._client = mock_client
        await client.close()
        mock_client.aclose.assert_called_once()