"""Comprehensive tests for transport_client_error.py — 100% coverage."""

import pytest
from taxonomy.transport_protocol_vo import TransportProtocol, TransportEndpoint
from taxonomy.transport_client_error import TransportError


class TestTransportError:
    def test_init(self):
        err = TransportError(
            protocol=TransportProtocol.HTTP,
            message="Connection refused"
        )
        assert err.protocol == TransportProtocol.HTTP
        assert err.message == "Connection refused"
        assert err.endpoint is None
        assert err.underlying_error == ""

    def test_with_endpoint(self):
        ep = TransportEndpoint(
            protocol=TransportProtocol.HTTP,
            address="http://localhost:8080"
        )
        err = TransportError(
            protocol=TransportProtocol.HTTP,
            message="Connection refused",
            endpoint=ep
        )
        assert err.endpoint == ep

    def test_with_underlying_error(self):
        err = TransportError(
            protocol=TransportProtocol.UNIX_SOCKET,
            message="Socket error",
            underlying_error="Connection refused"
        )
        assert err.underlying_error == "Connection refused"

    def test_str_without_endpoint(self):
        err = TransportError(
            protocol=TransportProtocol.STDIO,
            message="Failed"
        )
        assert str(err) == "[Stdio] Failed"

    def test_str_with_endpoint(self):
        ep = TransportEndpoint(
            protocol=TransportProtocol.HTTP,
            address="http://localhost:8080"
        )
        err = TransportError(
            protocol=TransportProtocol.HTTP,
            message="Connection refused",
            endpoint=ep
        )
        assert str(err) == "[HTTP] HTTP:http://localhost:8080 Connection refused"

    def test_model_dump(self):
        err = TransportError(
            protocol=TransportProtocol.UNIX_SOCKET,
            message="Socket not found"
        )
        dump = err.model_dump()
        assert dump["protocol"] == "UnixSocket"
        assert dump["message"] == "Socket not found"

    def test_frozen(self):
        err = TransportError(
            protocol=TransportProtocol.HTTP,
            message="Failed"
        )
        with pytest.raises(Exception):
            err.message = "Changed"
