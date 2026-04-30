"""Comprehensive tests for infrastructure/http_request_client.py — 100% coverage."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from infrastructure.http_request_client import HTTPClient


class TestHTTPClient:
    def test_init(self):
        client = HTTPClient("http://localhost:8080/execute")
        assert client.url == "http://localhost:8080/execute"
        assert client._client is None

    @pytest.mark.asyncio
    async def test_execute_success(self):
        client = HTTPClient("http://localhost:8080/execute")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"stdout": "output", "returncode": 0}

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.is_closed = True

        with patch("infrastructure.http_request_client.httpx.AsyncClient",
                   return_value=mock_client):
            result = await client.execute(["echo"], ".")
            assert result["returncode"] == 0

    @pytest.mark.asyncio
    async def test_execute_failure(self):
        client = HTTPClient("http://localhost:8080/execute")

        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=Exception("Connection error"))
        mock_client.is_closed = True

        with patch("infrastructure.http_request_client.httpx.AsyncClient",
                   return_value=mock_client):
            result = await client.execute(["echo"], ".")
            assert "error" in result

    @pytest.mark.asyncio
    async def test_close(self):
        client = HTTPClient("http://localhost:8080/execute")
        mock_client = MagicMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        client._client = mock_client
        await client.close()
        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_already_closed(self):
        client = HTTPClient("http://localhost:8080/execute")
        mock_client = MagicMock()
        mock_client.is_closed = True
        client._client = mock_client
        await client.close()
        # Should not raise

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        client = HTTPClient("http://localhost:8080/execute")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.is_closed = True

        with patch("infrastructure.http_request_client.httpx.AsyncClient",
                   return_value=mock_client):
            result = await client.health_check()
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        client = HTTPClient("http://localhost:8080/execute")

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=Exception("Down"))
        mock_client.is_closed = True

        with patch("infrastructure.http_request_client.httpx.AsyncClient",
                   return_value=mock_client):
            result = await client.health_check()
            assert "error" in result
