"""Comprehensive tests for transport_protocol_vo.py — 100% coverage."""

import pytest
from taxonomy.transport_protocol_vo import (
    TransportProtocol,
    TransportEndpoint,
)


# ─── TransportProtocol ───────────────────────────────────────────────────────

class TestTransportProtocol:
    def test_http(self):
        assert TransportProtocol.HTTP.value == "HTTP"

    def test_unix_socket(self):
        assert TransportProtocol.UNIX_SOCKET.value == "UnixSocket"

    def test_stdio(self):
        assert TransportProtocol.STDIO.value == "Stdio"

    def test_needs_desktop_commander_http(self):
        assert TransportProtocol.HTTP.needs_desktop_commander

    def test_needs_desktop_commander_unix(self):
        assert TransportProtocol.UNIX_SOCKET.needs_desktop_commander

    def test_needs_desktop_commander_stdio(self):
        assert not TransportProtocol.STDIO.needs_desktop_commander

    def test_from_string(self):
        assert TransportProtocol("HTTP") == TransportProtocol.HTTP
        assert TransportProtocol("UnixSocket") == TransportProtocol.UNIX_SOCKET
        assert TransportProtocol("Stdio") == TransportProtocol.STDIO

    def test_is_str_enum(self):
        assert TransportProtocol.HTTP == "HTTP"


# ─── TransportEndpoint ───────────────────────────────────────────────────────

class TestTransportEndpoint:
    def test_init(self):
        ep = TransportEndpoint(
            protocol=TransportProtocol.HTTP,
            address="http://localhost:8080"
        )
        assert ep.protocol == TransportProtocol.HTTP
        assert ep.address == "http://localhost:8080"

    def test_str(self):
        ep = TransportEndpoint(
            protocol=TransportProtocol.HTTP,
            address="http://localhost:8080"
        )
        assert str(ep) == "HTTP:http://localhost:8080"

    def test_from_url_http(self):
        ep = TransportEndpoint.from_url("http://localhost:8080")
        assert ep.protocol == TransportProtocol.HTTP
        assert ep.address == "http://localhost:8080"

    def test_from_url_https(self):
        ep = TransportEndpoint.from_url("https://example.com")
        assert ep.protocol == TransportProtocol.HTTP
        assert ep.address == "https://example.com"

    def test_from_url_stdio(self):
        ep = TransportEndpoint.from_url("stdio")
        assert ep.protocol == TransportProtocol.STDIO
        assert ep.address == "stdio"

    def test_from_url_unix_socket_absolute(self):
        ep = TransportEndpoint.from_url("/run/socket.sock")
        assert ep.protocol == TransportProtocol.UNIX_SOCKET
        assert ep.address == "/run/socket.sock"

    def test_from_url_unix_socket_relative(self):
        ep = TransportEndpoint.from_url("./socket.sock")
        assert ep.protocol == TransportProtocol.UNIX_SOCKET
        assert ep.address == "./socket.sock"

    def test_from_url_unknown_fallback_stdio(self):
        ep = TransportEndpoint.from_url("unknown_value")
        assert ep.protocol == TransportProtocol.STDIO
        assert ep.address == "stdio"

    def test_display_name_http(self):
        ep = TransportEndpoint(
            protocol=TransportProtocol.HTTP,
            address="http://localhost:8080"
        )
        assert ep.display_name == "HTTP(http://localhost:8080)"

    def test_display_name_unix(self):
        ep = TransportEndpoint(
            protocol=TransportProtocol.UNIX_SOCKET,
            address="/run/socket.sock"
        )
        assert ep.display_name == "Socket(/run/socket.sock)"

    def test_display_name_stdio(self):
        ep = TransportEndpoint(
            protocol=TransportProtocol.STDIO,
            address="stdio"
        )
        assert ep.display_name == "Stdio(direct)"

    def test_frozen(self):
        ep = TransportEndpoint(
            protocol=TransportProtocol.HTTP,
            address="http://localhost:8080"
        )
        with pytest.raises(Exception):
            ep.address = "http://other:9090"

    def test_model_dump(self):
        ep = TransportEndpoint(
            protocol=TransportProtocol.STDIO,
            address="stdio"
        )
        dump = ep.model_dump()
        assert dump["protocol"] == "Stdio"
        assert dump["address"] == "stdio"
