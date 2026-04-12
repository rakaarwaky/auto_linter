"""Additional tests for plugin_system to cover line 43 (dict entry points)."""

from unittest.mock import MagicMock, patch
import pytest
from infrastructure.plugin_system import (
    discover_plugins,
    register_custom_adapter,
    _custom_adapters,
)


class TestPluginSystemDictEntryPoints:
    """Test dict-based entry points (line 43)."""

    def setup_method(self):
        _custom_adapters.clear()

    def test_entry_points_dict_format(self):
        """Test when entry_points returns a dict (Python 3.9 style, line 43)."""
        mock_ep = MagicMock()
        mock_ep.name = "dict_adapter"
        mock_ep.load.return_value = MagicMock

        with patch("importlib.metadata.entry_points") as mock_eps:
            # Return a dict (Python 3.9 style)
            mock_eps.return_value = {"auto_linter.adapters": [mock_ep]}
            result = discover_plugins()
            assert "dict_adapter" in result

    def test_entry_points_dict_empty_group(self):
        """Test dict with missing group key."""
        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value = {}
            result = discover_plugins()
            assert result == {}
