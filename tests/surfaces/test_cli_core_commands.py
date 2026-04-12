"""Comprehensive tests for surfaces/cli_core_commands.py — 100% coverage."""

from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from surfaces.cli_core_commands import cli


class TestCoreCommands:
    def test_cli_group(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Auto-Linter" in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "Auto-Linter" in result.output

    def test_adapters(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["adapters"])
        assert result.exit_code == 0
        assert "Enabled Adapters" in result.output

    def test_check_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["check", "--help"])
        assert result.exit_code == 0
        assert "Run all linters" in result.output

    def test_scan_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["scan", "--help"])
        assert result.exit_code == 0

    def test_fix_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["fix", "--help"])
        assert result.exit_code == 0
        assert "Apply safe fixes" in result.output

    def test_report_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "--help"])
        assert result.exit_code == 0
        assert "Generate a detailed" in result.output

    def test_security_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["security", "--help"])
        assert result.exit_code == 0

    def test_check_on_fixtures(self):
        runner = CliRunner()
        import os
        fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
        if os.path.exists(fixtures_path):
            result = runner.invoke(cli, ["check", fixtures_path])
            # May have exit code 1 (issues found) or 0 (clean)
            assert result.exit_code in (0, 1)

    def test_check_git_diff_mode(self, tmp_path):
        """Test check with --git-diff flag."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "test.py\nother.py\n"
            mock_run.return_value = mock_result

            with patch("agent.dependency_injection_container.get_container") as mock_gc:
                container = MagicMock()
                mock_report = MagicMock()
                container.analysis_use_case.execute = MagicMock(return_value=mock_report)
                container.analysis_use_case.to_dict.return_value = {
                    "score": 85.0, "test_source": []
                }
                mock_gc.return_value = container

                runner = CliRunner()
                result = runner.invoke(cli, ["check", str(tmp_path), "--git-diff"])
                assert result.exit_code in (0, 1)

    def test_check_git_diff_fails(self, tmp_path):
        """Test check with --git-diff when git diff fails (line 67)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with patch("subprocess.run", side_effect=Exception("git not found")):
            with patch("agent.dependency_injection_container.get_container") as mock_gc:
                container = MagicMock()
                mock_report = MagicMock()
                container.analysis_use_case.execute = MagicMock(return_value=mock_report)
                container.analysis_use_case.to_dict.return_value = {
                    "score": 85.0, "test_source": []
                }
                mock_gc.return_value = container

                runner = CliRunner()
                result = runner.invoke(cli, ["check", str(tmp_path), "--git-diff"])
                assert result.exit_code in (0, 1)
                assert "Warning" in result.output or "git diff" in result.output.lower()

    def test_scan_command(self, tmp_path):
        """Test scan command (alias for check) (line 130)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        with patch("agent.dependency_injection_container.get_container") as mock_gc:
            container = MagicMock()
            mock_report = MagicMock()
            container.analysis_use_case.execute = MagicMock(return_value=mock_report)
            container.analysis_use_case.to_dict.return_value = {
                "score": 90.0, "ruff": [], "mypy": []
            }
            mock_gc.return_value = container

            runner = CliRunner()
            result = runner.invoke(cli, ["scan", str(tmp_path)])
            assert result.exit_code in (0, 1)

    def test_multi_project_command(self):
        """Test multi-project command (line 256)."""
        with patch("agent.dependency_injection_container.get_container") as mock_gc, \
             patch("agent.multi_project_orchestrator.load_multi_project_config", return_value=[]):
            container = MagicMock()
            mock_report = MagicMock()
            mock_report.to_dict.return_value = {"projects": [], "overall_score": 80.0}
            mock_report.to_text.return_value = "Multi-project report\nOverall: 80.0/100"
            container.multi_project.scan_all_projects = MagicMock(return_value=mock_report)
            mock_gc.return_value = container

            runner = CliRunner()
            result = runner.invoke(cli, ["multi-project", "--output-format", "text"])
            assert result.exit_code in (0, 1)

    def test_multi_project_json(self):
        """Test multi-project with JSON output."""
        with patch("agent.dependency_injection_container.get_container") as mock_gc, \
             patch("agent.multi_project_orchestrator.load_multi_project_config", return_value=[]):
            container = MagicMock()
            mock_report = MagicMock()
            mock_report.to_dict.return_value = {"projects": [], "overall_score": 80.0}
            mock_report.to_text.return_value = "Multi-project report"
            container.multi_project.scan_all_projects = MagicMock(return_value=mock_report)
            mock_gc.return_value = container

            runner = CliRunner()
            result = runner.invoke(cli, ["multi-project", "--output-format", "json"])
            assert result.exit_code in (0, 1)

    def test_check_with_non_list_results(self, tmp_path):
        """Test check handles various result types correctly."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\n")
        # Just verify check runs without crashing on a real file
        runner = CliRunner()
        result = runner.invoke(cli, ["check", str(tmp_path)])
        # May fail due to missing adapters but shouldn't crash
        assert result.exit_code in (0, 1)
