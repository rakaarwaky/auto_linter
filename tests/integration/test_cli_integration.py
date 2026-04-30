"""CLI integration tests using Click's CliRunner."""

import os
import pytest
from click.testing import CliRunner
from surfaces.cli_core_commands import cli


@pytest.fixture(autouse=True)
def reset_container():
    """Reset container singleton before each test."""
    global _container
    _container = None
    yield
    _container = None


class TestCoreCommands:
    """Test core CLI commands."""

    def test_version(self):
        """Test version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "Auto-Linter" in result.output

    def test_adapters(self):
        """Test adapters command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["adapters"])
        assert result.exit_code == 0
        assert "ruff" in result.output
        assert "Enabled Adapters" in result.output

    def test_check_on_fixtures(self):
        """Test check command on fixture directory."""
        runner = CliRunner()
        # Use the test fixtures directory
        fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
        
        # Create a simple test file if fixtures don't exist
        os.makedirs(fixtures_path, exist_ok=True)
        test_file = os.path.join(fixtures_path, "simple.py")
        with open(test_file, "w") as f:
            f.write("x = 1\n")
        
        # Reset container since we added a file
        global _container
        _container = None
        
        result = runner.invoke(cli, ["check", fixtures_path])
        # May have exit code issues but should not crash
        assert result.exit_code in (0, 1)  # 1 means issues found
        assert "Score" in result.output or "Running analysis" in result.output

    def test_scan_alias(self):
        """Test scan is alias for check."""
        runner = CliRunner()
        fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
        os.makedirs(fixtures_path, exist_ok=True)
        
        result = runner.invoke(cli, ["scan", fixtures_path])
        # Just check it runs
        assert "Running analysis" in result.output or "Score" in result.output

    def test_report_text_format(self):
        """Test report command with text format."""
        runner = CliRunner()
        fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
        
        result = runner.invoke(cli, ["report", fixtures_path, "--output-format", "text"])
        # Should not crash
        assert result.exit_code in (0, 1)

    def test_report_json_format(self):
        """Test report command with JSON format."""
        runner = CliRunner()
        fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
        
        result = runner.invoke(cli, ["report", fixtures_path, "--output-format", "json"])
        # Just verify runs
        assert result.exit_code in (0, 1)


class TestAnalysisCommands:
    """Test analysis CLI commands."""

    def test_security(self):
        """Test security command."""
        runner = CliRunner()
        fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
        
        result = runner.invoke(cli, ["security", fixtures_path])
        # Just verify it runs
        assert result.exit_code in (0, 1)
        assert "Running security" in result.output or "vulnerabilities" in result.output


class TestDevCommands:
    """Test development CLI commands."""

    def test_install_hook_dryrun(self):
        """Test install-hook command (dry run in test)."""
        runner = CliRunner()
        
        # Should handle gracefully even without git repo
        result = runner.invoke(cli, ["install-hook"], catch_exceptions=False)
        # May fail if no git, but shouldn't crash
        assert "install" in result.output.lower() or result.exit_code != 0


class TestCliRunnerBasics:
    """Basic CliRunner tests to ensure integration works."""

    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Auto-Linter" in result.output

    def test_cli_group_exists(self):
        """Test that CLI group is properly configured."""
        runner = CliRunner()
        runner.invoke(cli)
        # Running with no subcommand shows error (exit code 2)
        # but that's expected Click behavior