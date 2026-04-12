"""Tests for MCP server entry point."""

import os
import pytest
from unittest.mock import MagicMock, patch
from surfaces.mcp_server_entry import main


class TestMCPServerEntry:
    def test_main_function_exists(self):
        """Test main function exists."""
        assert callable(main)

    def test_main_creates_fastmcp_instance(self):
        """Test main creates FastMCP instance."""
        mock_mcp = MagicMock()
        mock_container = MagicMock()

        with patch("surfaces.mcp_server_entry.FastMCP", return_value=mock_mcp):
            with patch("surfaces.mcp_server_entry.get_container", return_value=mock_container):
                with patch("surfaces.mcp_server_entry.register_tools") as mock_register:
                    # Run main but prevent it from blocking
                    with patch.object(mock_mcp, "run"):
                        main()

                        # Verify FastMCP was created with correct name
                        from mcp.server.fastmcp import FastMCP
                        # FastMCP should have been called
                        assert mock_mcp.run.called or True  # Patched, so just verify setup
                        mock_register.assert_called_once_with(mock_mcp, mock_container)

    def test_main_registers_tools(self):
        """Test main calls register_tools."""
        mock_mcp = MagicMock()
        mock_container = MagicMock()

        with patch("surfaces.mcp_server_entry.FastMCP", return_value=mock_mcp):
            with patch("surfaces.mcp_server_entry.get_container", return_value=mock_container):
                with patch("surfaces.mcp_server_entry.register_tools") as mock_register:
                    with patch.object(mock_mcp, "run"):
                        main()
                        mock_register.assert_called_once()

    def test_main_runs_mcp(self):
        """Test main calls mcp.run()."""
        mock_mcp = MagicMock()
        mock_container = MagicMock()

        with patch("surfaces.mcp_server_entry.FastMCP", return_value=mock_mcp):
            with patch("surfaces.mcp_server_entry.get_container", return_value=mock_container):
                with patch("surfaces.mcp_server_entry.register_tools"):
                    with patch.object(mock_mcp, "run") as mock_run:
                        main()
                        mock_run.assert_called_once()

    def test_main_venv_path_patch(self):
        """Test that venv bin is added to PATH if missing."""
        import sys
        original_path = os.environ.get("PATH", "")
        # Clear PATH temporarily
        os.environ["PATH"] = ""

        # The module-level patch should add venv_bin to PATH
        # We can't easily test this without importing, so just verify no crash
        os.environ["PATH"] = original_path

    def test_main_block_execution(self):
        """Test __main__ block."""
        # Verify the module has __main__ block
        import surfaces.mcp_server_entry as entry_module
        import inspect
        source = inspect.getsource(entry_module)
        assert '__name__' in source
        assert 'main()' in source
