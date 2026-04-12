"""Comprehensive tests for surfaces/cli_setup_commands.py."""

import shutil
from click.testing import CliRunner
from unittest.mock import patch
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
        """Test when hermes exists but auto-linter doesn't."""
        def which_side_effect(name):
            if name == "hermes":
                return "/usr/bin/hermes"
            return None
        mock_which.side_effect = which_side_effect
        runner = CliRunner()
        result = runner.invoke(setup, ["hermes"])
        assert result.exit_code == 0
        assert "auto-linter" in result.output.lower()


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

    def test_mcp_config_vscode(self):
        from surfaces.cli_setup_commands import _mcp_config_vscode
        config = _mcp_config_vscode("auto")
        assert "mcp" in config
        assert "servers" in config["mcp"]

    def test_check_http_failure(self):
        from surfaces.cli_setup_commands import _check_http
        result = _check_http("http://localhost:99999/health")
        assert result is False
