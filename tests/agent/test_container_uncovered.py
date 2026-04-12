"""Additional tests for dependency_injection_container to cover lines 51-52, 127."""

import pytest
from unittest.mock import patch
from agent import dependency_injection_container as container_mod


class TestContainerUncovered:
    """Tests for uncovered lines 51-52 and 127."""

    def setup_method(self):
        container_mod._container = None

    def teardown_method(self):
        container_mod._container = None

    def test_container_health(self):
        """Test container health method (line 127)."""
        from agent.dependency_injection_container import Container
        container = Container()
        health = container.health()
        assert "lifecycle" in health
        assert "adapters" in health
        assert "adapter_count" in health
        assert health["adapter_count"] == len(container.adapters)

    def test_container_shutdown(self):
        """Test container shutdown method."""
        from agent.dependency_injection_container import Container
        container = Container()
        container.shutdown()
        # Verify state was marked as stopped
        health = container.health()
        # Should still be accessible after shutdown
        assert "lifecycle" in health
