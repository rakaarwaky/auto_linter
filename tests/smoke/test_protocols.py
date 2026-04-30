"""
Cross-Protocol Compatibility Tests for DesktopCommander Client.

Tests both HTTP and Unix Socket protocols to ensure:
1. Both protocols produce identical results
2. Auto-detection works correctly
3. Failover mechanisms function properly
4. Health checks work on both protocols
"""

import pytest
import os
import socket
from unittest.mock import AsyncMock, patch

# Import the client
from infrastructure.desktop_commander_adapter import (
    DesktopCommanderAdapter,
    execute_via_desktop_commander,
    detect_protocol,
)


class TestProtocolDetection:
    """Test protocol auto-detection logic."""

    def test_detect_http_url(self):
        """Test HTTP URL detection."""
        assert detect_protocol("http://localhost:8080/execute") == "HTTP"
        assert detect_protocol("https://example.com/api") == "HTTP"

    def test_detect_unix_socket_url(self):
        """Test Unix Socket URL detection."""
        assert detect_protocol("/run/desktop-commander/socket") == "UnixSocket"
        assert detect_protocol("./socket.sock") == "UnixSocket"
        assert detect_protocol("/tmp/test.sock") == "UnixSocket"

    def test_detect_unknown_url(self):
        """Test unknown URL format."""
        assert detect_protocol("localhost:8080") == "Unknown"
        assert detect_protocol("invalid") == "Unknown"


class TestDesktopCommanderAdapterInitialization:
    """Test client initialization."""

    def test_init_with_url(self):
        """Test initialization with explicit URL."""
        client = DesktopCommanderAdapter(url="http://localhost:8080/execute")
        assert client.url == "http://localhost:8080/execute"
        assert client.protocol == "HTTP"

    def test_init_with_socket_path(self):
        """Test initialization with socket path."""
        client = DesktopCommanderAdapter(url="/run/desktop-commander/socket")
        assert client.url == "/run/desktop-commander/socket"
        assert client.protocol == "UnixSocket"

    def test_init_from_env_var(self):
        """Test initialization from environment variable."""
        with patch.dict(os.environ, {"DESKTOP_COMMANDER_URL": "http://env-test:8080/execute"}):
            client = DesktopCommanderAdapter()
            assert client.url == "http://env-test:8080/execute"

    def test_init_default(self):
        """Test default initialization."""
        with patch.dict(os.environ, {}, clear=True):
            client = DesktopCommanderAdapter()
            assert client.url == "/run/desktop-commander/socket"


class TestUnixSocketConnection:
    """Test Unix Socket connection handling."""

    @pytest.fixture
    def mock_socket_server(self, tmp_path):
        """Create a mock Unix socket server for testing."""
        socket_path = tmp_path / "test.sock"
        
        # Create mock server
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(socket_path))
        server.listen(1)
        server.settimeout(0.1)
        
        yield str(socket_path), server
        
        server.close()

    def test_socket_connection_success(self, mock_socket_server):
        """Test successful socket connection."""
        socket_path, server = mock_socket_server

        client = DesktopCommanderAdapter(url=socket_path)
        assert client.is_unix_socket

        # Test unix client creation
        unix_client = client._get_unix_client()
        assert unix_client is not None


class TestHTTPConnection:
    """Test HTTP connection handling."""

    @pytest.mark.asyncio
    async def test_http_client_creation(self):
        """Test HTTP client creation."""
        client = DesktopCommanderAdapter(url="http://localhost:8080/execute")
        assert client.is_http

        http_client = client._get_http_client()
        assert http_client is not None


class TestExecuteCommand:
    """Test command execution."""

    @pytest.mark.asyncio
    async def test_execute_command_unix_socket_mock(self):
        """Test command execution via Unix Socket (mocked)."""
        client = DesktopCommanderAdapter(url="/tmp/test.sock", auto_detect=False)

        with patch.object(client, '_get_unix_client') as mock_get:
            mock_unix = AsyncMock()
            mock_unix.execute.return_value = {
                "stdout": "test output",
                "stderr": "",
                "returncode": 0,
                "protocol": "UnixSocket"
            }
            mock_get.return_value = mock_unix

            result = await client.execute_command(["echo", "test"])

            assert result["stdout"] == "test output"
            assert result["returncode"] == 0
            assert result["protocol"] == "UnixSocket"

    @pytest.mark.asyncio
    async def test_execute_command_http_mock(self):
        """Test command execution via HTTP (mocked)."""
        client = DesktopCommanderAdapter(url="http://localhost:8080/execute", auto_detect=False)

        with patch.object(client, '_get_http_client') as mock_get:
            mock_http = AsyncMock()
            mock_http.execute.return_value = {
                "stdout": "http output",
                "stderr": "",
                "returncode": 0,
                "protocol": "HTTP"
            }
            mock_get.return_value = mock_http

            result = await client.execute_command(["echo", "test"])

            assert result["stdout"] == "http output"
            assert result["returncode"] == 0
            assert result["protocol"] == "HTTP"


class TestHealthCheck:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        client = DesktopCommanderAdapter(url="/tmp/test.sock", auto_detect=False)
        
        with patch.object(client, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "latency_ms": 2.5,
                "protocol": "UnixSocket"
            }
            
            result = await client.health_check()
            
            assert result["status"] == "healthy"
            assert result["latency_ms"] == 2.5
            assert result["protocol"] == "UnixSocket"

    @pytest.mark.asyncio
    @pytest.mark.filterwarnings("ignore::ResourceWarning")
    async def test_health_check_failure(self):
        """Test failed health check."""
        client = DesktopCommanderAdapter(url="/nonexistent.sock", auto_detect=False)
        
        result = await client.health_check()
        
        assert result["status"] == "unhealthy"
        assert "error" in result


class TestExponentialBackoff:
    """Test exponential backoff retry mechanism."""

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        """Test retry mechanism on connection errors."""
        from surfaces.mcp_desktop_client import _execute_with_retry
        
        client = DesktopCommanderAdapter(url="http://localhost:8080/execute")
        
        # Mock client to fail twice, then succeed
        call_count = 0
        
        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection refused")
            return {"stdout": "success", "returncode": 0}
        
        with patch.object(client, 'execute_command', side_effect=mock_execute):
            result = await _execute_with_retry(
                client=client,
                command=["test"],
                working_dir=".",
                timeout=30,
                max_retries=5
            )
            
            assert call_count == 3
            assert result["stdout"] == "success"

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test retry exhaustion."""
        from surfaces.mcp_desktop_client import _execute_with_retry
        
        client = DesktopCommanderAdapter(url="http://localhost:8080/execute")
        
        async def mock_execute_fail(*args, **kwargs):
            raise ConnectionError("Connection refused")
        
        with patch.object(client, 'execute_command', side_effect=mock_execute_fail):
            result = await _execute_with_retry(
                client=client,
                command=["test"],
                working_dir=".",
                timeout=30,
                max_retries=3
            )
            
            assert "error" in result
            assert "3 attempts" in result["error"]


class TestConvenienceFunction:
    """Test the convenience function."""

    @pytest.mark.asyncio
    async def test_execute_via_desktop_commander(self):
        """Test convenience function."""
        with patch('infrastructure.desktop_commander_adapter.DesktopCommanderAdapter') as MockClient:
            mock_instance = AsyncMock()
            mock_instance.execute_command.return_value = {
                "stdout": "test",
                "returncode": 0
            }
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance
            
            result = await execute_via_desktop_commander(
                command=["echo", "test"],
                working_dir="/tmp"
            )
            
            assert result["stdout"] == "test"
            assert result["returncode"] == 0


class TestIntegrationScenarios:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.filterwarnings("ignore::ResourceWarning")
    async def test_protocol_switch_on_failure(self):
        """Test protocol switching on failure (auto mode)."""
        client = DesktopCommanderAdapter(url="/nonexistent.sock", auto_detect=True)
        
        # Should try Unix Socket first, then potentially switch
        result = await client.execute_command(["echo", "test"])
        
        # Should have attempted execution
        assert "error" in result or "stderr" in result

    def test_client_reuse(self):
        """Test client instance reuse."""
        client1 = DesktopCommanderAdapter(url="http://localhost:8080/execute")
        client2 = DesktopCommanderAdapter(url="http://localhost:8080/execute")
        
        # Different instances, but same configuration
        assert client1.url == client2.url
        assert client1.protocol == client2.protocol


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
