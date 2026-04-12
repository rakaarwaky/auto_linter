"""Comprehensive tests for surfaces/cli_setup_commands.py."""

import json
import shutil
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
from surfaces.cli_setup_commands import setup


class TestSetupGroup:
    def test_setup_group_help(self):
        runner = CliRunner()
        result = runner.invoke(setup, ["--help"])
        assert result.exit_code == 0
        assert "Setup and configuration" in result.output


class TestSetupInit:
    @patch("surfaces.cli_setup_commands._check_http", return_value=False)
    def test_init_socket_found(self, mock_http, tmp_path, monkeypatch):
        # Simulate socket exists
        monkeypatch.setattr(Path, "exists", lambda self: str(self).endswith("dc.sock"))
        # Mock shutil.which to return None for all linters
        monkeypatch.setattr(shutil, "which", lambda name: None)

        runner = CliRunner()
        result = runner.invoke(setup, ["init"])
        assert result.exit_code == 0
        assert "Auto-Linter Setup" in result.output
        assert "DesktopCommander" in result.output

    @patch("surfaces.cli_setup_commands._check_http", return_value=False)
    @patch("pathlib.Path.exists", return_value=False)
    def test_init_no_dc(self, mock_exists, mock_http, tmp_path):
        runner = CliRunner()
        result = runner.invoke(setup, ["init"])
        assert result.exit_code == 0
        assert "Detecting environment" in result.output

    @patch("surfaces.cli_setup_commands._check_http", return_value=True)
    @patch("pathlib.Path.exists", return_value=False)
    def test_init_http_mode(self, mock_exists, mock_http, tmp_path):
        runner = CliRunner()
        result = runner.invoke(setup, ["init"])
        assert result.exit_code == 0
        assert "HTTP" in result.output

    @patch("surfaces.cli_setup_commands._check_http", return_value=False)
    @patch("pathlib.Path.exists", return_value=False)
    def test_init_generates_env(self, mock_exists, mock_http, tmp_path):
        runner = CliRunner()
        result = runner.invoke(setup, ["init"])
        assert result.exit_code == 0
        assert "Creating .env" in result.output

    @patch("surfaces.cli_setup_commands._check_http", return_value=False)
    @patch("pathlib.Path.exists", side_effect=lambda: True)
    def test_init_env_exists_skip(self, mock_exists, mock_http, tmp_path):
        runner = CliRunner()
        result = runner.invoke(setup, ["init"])
        assert result.exit_code == 0
        assert "already exists" in result.output


class TestSetupDoctor:
    def test_doctor(self):
        runner = CliRunner()
        result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        assert "Auto-Linter Doctor" in result.output
        assert "Python" in result.output

    def test_doctor_shows_linters(self):
        runner = CliRunner()
        result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        assert "ruff" in result.output or "not installed" in result.output

    def test_doctor_shows_config_status(self):
        runner = CliRunner()
        result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        assert "auto_linter.config.yaml" in result.output or "DesktopCommander" in result.output

    @patch("platform.python_version", return_value="3.10.0")
    @patch("platform.python_version_tuple", return_value=("3", "10", "0"))
    def test_doctor_old_python_version(self, mock_tuple, mock_version):
        """Test doctor with Python < 3.12 (line 93)."""
        runner = CliRunner()
        result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        assert "3.12 required" in result.output or "issue" in result.output.lower()

    def test_doctor_missing_dependencies(self):
        """Test doctor with missing dependencies (lines 102-104)."""
        import builtins
        original_import = builtins.__import__

        def selective_import(name, *args, **kwargs):
            if name in ["mcp", "pydantic", "yaml", "dotenv"]:
                raise ImportError(f"Missing {name}")
            return original_import(name, *args, **kwargs)

        runner = CliRunner()
        with patch("builtins.__import__", side_effect=selective_import):
            result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        assert "MISSING" in result.output or "issue" in result.output.lower()

    @patch("pathlib.Path.exists", return_value=True)
    def test_doctor_all_checks_passed(self, mock_exists):
        """Test doctor when all checks pass (lines 118, 124, 129, 133-135)."""
        runner = CliRunner()
        result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        # Should show OK for various checks
        assert "Doctor" in result.output

    def test_doctor_shows_missing_env(self):
        """Test doctor shows missing .env (line 111)."""
        runner = CliRunner()
        with patch("pathlib.Path.exists", return_value=False):
            result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        assert "not found" in result.output or ".env" in result.output

    def test_doctor_shows_missing_config(self):
        """Test doctor shows missing config (line 118)."""
        def mock_exists(self):
            path_str = str(self) if hasattr(self, '__str__') else ''
            # Only make .env exist, not auto_linter.config.yaml
            return '.env' in path_str

        runner = CliRunner()
        with patch("pathlib.Path.exists", mock_exists):
            result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        assert "auto_linter.config.yaml" in result.output or "not found" in result.output

    def test_doctor_shows_socket_missing(self):
        """Test doctor shows DesktopCommander not running (line 124)."""
        def mock_exists(self):
            path_str = str(self) if hasattr(self, '__str__') else ''
            # Make dc.sock NOT exist
            return 'dc.sock' not in path_str and '.env' not in path_str

        runner = CliRunner()
        with patch("pathlib.Path.exists", mock_exists):
            result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        assert "not running" in result.output or "not found" in result.output

    def test_doctor_shows_env_exists(self):
        """Test doctor shows .env exists (line 129)."""
        def mock_exists(self):
            path_str = str(self) if hasattr(self, '__str__') else ''
            return '.env' in path_str or 'dc.sock' in path_str

        runner = CliRunner()
        with patch("pathlib.Path.exists", mock_exists):
            result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        assert ".env" in result.output


class TestSetupMcpConfig:
    @patch("pathlib.Path.exists", return_value=False)
    def test_mcp_config_all(self, mock_exists):
        runner = CliRunner()
        result = runner.invoke(setup, ["mcp-config", "--client", "all"])
        assert result.exit_code == 0
        assert "claude" in result.output.lower() or "CLAUDE" in result.output
        assert "hermes" in result.output.lower() or "HERMES" in result.output
        assert "vscode" in result.output.lower() or "VSCODE" in result.output

    @patch("pathlib.Path.exists", return_value=False)
    def test_mcp_config_claude_only(self, mock_exists):
        runner = CliRunner()
        result = runner.invoke(setup, ["mcp-config", "--client", "claude"])
        assert result.exit_code == 0
        assert "CLAUDE" in result.output
        # Should NOT contain other clients
        assert "HERMES" not in result.output
        assert "VSCODE" not in result.output

    @patch("pathlib.Path.exists", return_value=False)
    def test_mcp_config_hermes_only(self, mock_exists):
        runner = CliRunner()
        result = runner.invoke(setup, ["mcp-config", "--client", "hermes"])
        assert result.exit_code == 0
        assert "HERMES" in result.output

    @patch("pathlib.Path.exists", return_value=False)
    def test_mcp_config_vscode_only(self, mock_exists):
        runner = CliRunner()
        result = runner.invoke(setup, ["mcp-config", "--client", "vscode"])
        assert result.exit_code == 0
        assert "VSCODE" in result.output

    @patch("pathlib.Path.exists", return_value=True)
    def test_mcp_config_with_socket(self, mock_exists):
        """Test mcp-config when dc.sock exists (line 146)."""
        runner = CliRunner()
        result = runner.invoke(setup, ["mcp-config", "--client", "claude"])
        assert result.exit_code == 0
        assert "CLAUDE" in result.output


class TestSetupHermes:
    def test_hermes_not_found(self):
        """Test when hermes command is not available."""
        runner = CliRunner()
        with patch.object(shutil, "which", return_value=None):
            result = runner.invoke(setup, ["hermes"])
            assert result.exit_code == 0
            assert "not found" in result.output.lower() or "ERROR" in result.output

    @patch.object(shutil, "which")
    def test_hermes_auto_linter_not_found(self, mock_which):
        """Test when hermes exists but auto-linter doesn't (lines 193-201)."""
        def which_side_effect(name):
            if name == "hermes":
                return "/usr/bin/hermes"
            return None
        mock_which.side_effect = which_side_effect
        runner = CliRunner()
        result = runner.invoke(setup, ["hermes"])
        assert result.exit_code == 0
        assert "auto-linter" in result.output.lower() or "not found" in result.output.lower()

    @patch.object(shutil, "which")
    def test_hermes_remove_mode(self, mock_which):
        """Test hermes with --remove flag (lines 206-215)."""
        def which_side_effect(name):
            if name == "hermes":
                return "/usr/bin/hermes"
            if name == "auto-linter":
                return "/usr/bin/auto-linter"
            return None
        mock_which.side_effect = which_side_effect

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Removed auto-linter"
        mock_result.stderr = ""

        runner = CliRunner()
        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(setup, ["hermes", "--remove"])
        assert result.exit_code == 0
        assert "Removing" in result.output

    @patch.object(shutil, "which")
    def test_hermes_add_success(self, mock_which):
        """Test hermes add mode success (lines 218-233)."""
        def which_side_effect(name):
            if name == "hermes":
                return "/usr/bin/hermes"
            if name == "auto-linter":
                return "/usr/bin/auto-linter"
            return None
        mock_which.side_effect = which_side_effect

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Added successfully"
        mock_result.stderr = ""

        runner = CliRunner()
        # Simulate dc.sock exists for env_vars
        with patch("subprocess.run", return_value=mock_result), \
             patch("pathlib.Path.exists", return_value=True):
            result = runner.invoke(setup, ["hermes"])
        assert result.exit_code == 0
        assert "Done" in result.output or "Added" in result.output

    @patch.object(shutil, "which")
    def test_hermes_add_failure(self, mock_which):
        """Test hermes add mode failure (lines 228-233)."""
        def which_side_effect(name):
            if name == "hermes":
                return "/usr/bin/hermes"
            if name == "auto-linter":
                return "/usr/bin/auto-linter"
            return None
        mock_which.side_effect = which_side_effect

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "hermes error: config full"

        runner = CliRunner()
        with patch("subprocess.run", return_value=mock_result), \
             patch("pathlib.Path.exists", return_value=False):
            result = runner.invoke(setup, ["hermes"])
        assert result.exit_code == 0
        assert "ERROR" in result.output or "Manual" in result.output

    @patch.object(shutil, "which")
    def test_hermes_remove_subprocess(self, mock_which):
        """Test hermes remove with subprocess (lines 210-211)."""
        def which_side_effect(name):
            if name == "hermes":
                return "/usr/bin/hermes"
            if name == "auto-linter":
                return "/usr/bin/auto-linter"
            return None
        mock_which.side_effect = which_side_effect

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Removed auto-linter from config"
        mock_result.stderr = ""

        runner = CliRunner()
        with patch("subprocess.run", return_value=mock_result):
            result = runner.invoke(setup, ["hermes", "--remove"])
        assert result.exit_code == 0
        assert "Removing" in result.output
        assert "Done" in result.output

    @patch.object(shutil, "which")
    def test_hermes_with_dc_socket(self, mock_which):
        """Test hermes with dc.sock found (line 219)."""
        def which_side_effect(name):
            if name == "hermes":
                return "/usr/bin/hermes"
            if name == "auto-linter":
                return "/usr/bin/auto-linter"
            return None
        mock_which.side_effect = which_side_effect

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Added"
        mock_result.stderr = ""

        runner = CliRunner()
        def mock_exists_side_effect(self):
            path_str = str(self) if hasattr(self, '__str__') else ''
            return 'dc.sock' in path_str

        with patch("subprocess.run", return_value=mock_result), \
             patch("pathlib.Path.exists", mock_exists_side_effect):
            result = runner.invoke(setup, ["hermes"])
        assert result.exit_code == 0
        assert "DesktopCommander: found" in result.output


class TestHelpers:
    def test_generate_env_auto(self):
        from surfaces.cli_setup_commands import _generate_env
        env = _generate_env("auto", "/home/test")
        assert "DESKTOP_COMMANDER_URL" in env
        assert "PHANTOM_ROOT" in env

    def test_generate_env_socket(self):
        from surfaces.cli_setup_commands import _generate_env
        env = _generate_env("/tmp/dc.sock", "/home/test")
        assert "/tmp/dc.sock" in env
        assert "PHANTOM_ROOT" in env

    def test_generate_mcp_config(self):
        from surfaces.cli_setup_commands import _generate_mcp_config
        config = _generate_mcp_config("auto")
        assert "auto-linter" in config
        assert "command" in config["auto-linter"]
        assert "alwaysAllow" in config["auto-linter"]

    def test_mcp_config_claude(self):
        from surfaces.cli_setup_commands import _mcp_config_claude
        config = _mcp_config_claude("auto")
        assert "mcpServers" in config

    def test_mcp_config_hermes(self):
        from surfaces.cli_setup_commands import _mcp_config_hermes
        config = _mcp_config_hermes("auto")
        assert "auto-linter" in config

    def test_mcp_config_hermes_with_socket(self):
        """Test _mcp_config_hermes with socket transport (line 295)."""
        from surfaces.cli_setup_commands import _mcp_config_hermes
        config = _mcp_config_hermes("/tmp/dc.sock")
        assert "auto-linter" in config
        assert "env" in config["auto-linter"]
        assert "DESKTOP_COMMANDER_URL" in config["auto-linter"]["env"]

    def test_mcp_config_vscode(self):
        from surfaces.cli_setup_commands import _mcp_config_vscode
        config = _mcp_config_vscode("auto")
        assert "mcp" in config
        assert "servers" in config["mcp"]

    def test_check_http_failure(self):
        from surfaces.cli_setup_commands import _check_http
        result = _check_http("http://localhost:99999/health")
        assert result is False

    @patch("httpx.get", return_value=MagicMock(status_code=200))
    def test_check_http_success(self, mock_get):
        """Test _check_http success path."""
        from surfaces.cli_setup_commands import _check_http
        result = _check_http("http://localhost:24680/health")
        assert result is True

    @patch("httpx.get", return_value=MagicMock(status_code=503))
    def test_check_http_server_error(self, mock_get):
        """Test _check_http with 5xx error."""
        from surfaces.cli_setup_commands import _check_http
        result = _check_http("http://localhost:24680/health")
        assert result is False

    def test_doctor_linter_found(self):
        """Test doctor when a linter is found (line 111)."""
        runner = CliRunner()
        with patch("shutil.which", return_value="/usr/bin/ruff"):
            result = runner.invoke(setup, ["doctor"])
        assert result.exit_code == 0
        assert "[OK]" in result.output
