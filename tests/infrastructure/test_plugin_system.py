"""Tests for plugin_system module."""

import pytest
from unittest.mock import MagicMock, patch
from infrastructure.plugin_system import (
    discover_plugins,
    register_custom_adapter,
    unregister_custom_adapter,
    get_custom_adapter,
    list_custom_adapters,
    load_all_plugins,
    _custom_adapters,
)


class TestDiscoverPlugins:
    def test_no_entry_points(self):
        """Returns empty dict when no entry points found."""
        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = []
            result = discover_plugins()
            assert result == {}

    def test_entry_points_found(self):
        """Discovers and returns entry points."""
        mock_ep = MagicMock()
        mock_ep.name = "my_adapter"
        mock_ep.load.return_value = MagicMock

        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [mock_ep]
            result = discover_plugins()
            assert "my_adapter" in result

    def test_entry_point_load_failure(self):
        """Handles load failure gracefully."""
        mock_ep = MagicMock()
        mock_ep.name = "broken_adapter"
        mock_ep.load.side_effect = ImportError("No module")

        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value.select.return_value = [mock_ep]
            result = discover_plugins()
            assert result == {}


class TestCustomAdapterRegistry:
    def setup_method(self):
        """Clear registry before each test."""
        _custom_adapters.clear()

    def test_register_adapter(self):
        """Registers an adapter successfully."""
        adapter_class = MagicMock
        register_custom_adapter("test_adapter", adapter_class)
        assert get_custom_adapter("test_adapter") is adapter_class

    def test_unregister_adapter(self):
        """Unregisters an adapter successfully."""
        adapter_class = MagicMock
        register_custom_adapter("test_adapter", adapter_class)
        result = unregister_custom_adapter("test_adapter")
        assert result is adapter_class
        assert get_custom_adapter("test_adapter") is None

    def test_unregister_nonexistent(self):
        """Unregistering non-existent adapter returns None."""
        result = unregister_custom_adapter("nonexistent")
        assert result is None

    def test_get_nonexistent_adapter(self):
        """Getting non-existent adapter returns None."""
        assert get_custom_adapter("nonexistent") is None

    def test_list_custom_adapters(self):
        """Lists all registered adapters."""
        register_custom_adapter("adapter1", MagicMock)
        register_custom_adapter("adapter2", MagicMock)
        result = list_custom_adapters()
        assert len(result) == 2
        names = [a["name"] for a in result]
        assert "adapter1" in names
        assert "adapter2" in names


class TestLoadAllPlugins:
    def setup_method(self):
        _custom_adapters.clear()

    def test_load_all_plugins_empty(self):
        """Returns empty dict when no plugins."""
        with patch("infrastructure.plugin_system.discover_plugins", return_value={}):
            result = load_all_plugins()
            assert result == {}

    def test_load_all_plugins_with_discovery(self):
        """Discovers and registers plugins."""
        mock_adapter = MagicMock
        with patch("infrastructure.plugin_system.discover_plugins", return_value={"found": mock_adapter}):
            result = load_all_plugins()
            assert "found" in result
            assert get_custom_adapter("found") is mock_adapter
