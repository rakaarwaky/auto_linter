"""Additional tests for HTTP client to cover line 93 (health_check non-200 response)."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from infrastructure.http_request_client import HTTPClient


class TestHTTPClientHealthCheckNon200:
    """Test health_check when response is not 200 (line 93)."""

    @pytest.mark.asyncio
    async def test_health_check_non_200_falls_back_to_execute(self):
        """When health endpoint returns non-200, falls back to execute."""
        client = HTTPClient("http://localhost:8080/execute")
        
        non_200_response = MagicMock()
        non_200_response.status_code = 503
        non_200_response.raise_for_status.side_effect = Exception("Server Error")

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=non_200_response)
        mock_client.is_closed = True
        
        # Mock execute to return success
        mock_client.post = AsyncMock(return_value=MagicMock(
            json=MagicMock(return_value={"stdout": "health", "returncode": 0}),
            raise_for_status=MagicMock()
        ))

        with patch("infrastructure.http_request_client.httpx.AsyncClient",
                   return_value=mock_client):
            result = await client.health_check()
            # Should fall back to execute and return healthy
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_non_200_execute_also_fails(self):
        """When health returns non-200 and execute also fails."""
        client = HTTPClient("http://localhost:8080/execute")
        
        non_200_response = MagicMock()
        non_200_response.status_code = 503

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=non_200_response)
        mock_client.is_closed = True
        
        # Mock execute to return failure
        mock_client.post = AsyncMock(return_value=MagicMock(
            json=MagicMock(return_value={"stdout": "", "returncode": 1, "stderr": "fail"}),
            raise_for_status=MagicMock()
        ))

        with patch("infrastructure.http_request_client.httpx.AsyncClient",
                   return_value=mock_client):
            result = await client.health_check()
            assert result["status"] == "unhealthy"
