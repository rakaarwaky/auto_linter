"""Tests for surface layer CLI commands."""

from click.testing import CliRunner
from surfaces.cli_core_commands import cli


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0


def test_cli_adapters():
    runner = CliRunner()
    result = runner.invoke(cli, ["adapters"])
    assert result.exit_code == 0
    assert "ruff" in result.output


def test_cli_check_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["check", "--help"])
    assert result.exit_code == 0
    assert "Run all linters" in result.output


def test_cli_fix_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["fix", "--help"])
    assert result.exit_code == 0
    assert "Apply safe fixes" in result.output


def test_cli_report_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["report", "--help"])
    assert result.exit_code == 0
    assert "Generate a detailed" in result.output


def test_cli_security_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["security", "--help"])
    assert result.exit_code == 0
    assert "security" in result.output.lower()
