"""Tests for agent/multi_project_orchestrator.py — agent coordinates multi-project scans."""

import pytest
import json
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from agent.multi_project_orchestrator import (
    ProjectResult,
    AggregatedResults,
    find_projects,
    load_multi_project_config,
    MultiProjectOrchestrator,
)


# ── ProjectResult dataclass ───────────────────────────────────────

class TestProjectResult:
    def test_default_values(self):
        pr = ProjectResult(path="/tmp/test", score=85.0, is_passing=True)
        assert pr.path == "/tmp/test"
        assert pr.score == 85.0
        assert pr.is_passing is True
        assert pr.issues == []
        assert pr.adapters == []

    def test_with_issues(self):
        pr = ProjectResult(
            path="/tmp/test", score=0.0, is_passing=False,
            issues=[{"error": "fail"}], adapters=["ruff"]
        )
        assert len(pr.issues) == 1
        assert pr.adapters == ["ruff"]


# ── AggregatedResults dataclass ──────────────────────────────────

class TestAggregatedResults:
    def test_default_values(self):
        ar = AggregatedResults()
        assert ar.total_projects == 0
        assert ar.passing_projects == 0
        assert ar.failing_projects == 0
        assert ar.average_score == 0.0
        assert ar.projects == []

    def test_to_dict_empty(self):
        ar = AggregatedResults()
        d = ar.to_dict()
        assert d["summary"]["total_projects"] == 0
        assert d["projects"] == []

    def test_to_dict_with_projects(self):
        projects = [
            ProjectResult(path="/a", score=90.0, is_passing=True, adapters=["ruff"]),
            ProjectResult(path="/b", score=60.0, is_passing=False, issues=[{"e": 1}]),
        ]
        ar = AggregatedResults(
            projects=projects, total_projects=2,
            passing_projects=1, failing_projects=1, average_score=75.0
        )
        d = ar.to_dict()
        assert d["summary"]["total_projects"] == 2
        assert d["summary"]["passing_projects"] == 1
        assert d["summary"]["failing_projects"] == 1
        assert d["summary"]["average_score"] == 75.0
        assert len(d["projects"]) == 2
        assert d["projects"][0]["issues_count"] == 0
        assert d["projects"][1]["issues_count"] == 1
        assert d["projects"][0]["adapters"] == ["ruff"]

    def test_to_text_empty(self):
        ar = AggregatedResults()
        text = ar.to_text()
        assert "Multi-Project Scan Results" in text

    def test_to_text_with_results(self):
        projects = [
            ProjectResult(path="/a", score=90.0, is_passing=True),
            ProjectResult(path="/b", score=60.0, is_passing=False),
        ]
        ar = AggregatedResults(
            projects=projects, total_projects=2,
            passing_projects=1, failing_projects=1, average_score=75.0
        )
        text = ar.to_text()
        assert "90.0" in text
        assert "60.0" in text
        assert "Summary" in text


# ── find_projects ─────────────────────────────────────────────────

class TestFindProjects:
    def test_empty_directory(self):
        d = tempfile.mkdtemp()
        try:
            result = find_projects(d)
            assert result == []
        finally:
            shutil.rmtree(d)

    def test_finds_json_config(self):
        d = tempfile.mkdtemp()
        try:
            subdir = os.path.join(d, "proj1")
            os.makedirs(subdir)
            with open(os.path.join(subdir, ".auto_linter.json"), "w") as f:
                f.write("{}")
            result = find_projects(d)
            assert len(result) == 1
            assert result[0] == Path(subdir)
        finally:
            shutil.rmtree(d)

    def test_finds_yaml_config(self):
        d = tempfile.mkdtemp()
        try:
            subdir = os.path.join(d, "proj2")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "auto_linter.config.yaml"), "w") as f:
                f.write("{}")
            result = find_projects(d)
            assert len(result) == 1
            assert result[0] == Path(subdir)
        finally:
            shutil.rmtree(d)

    def test_no_duplicates_json_and_yaml(self):
        d = tempfile.mkdtemp()
        try:
            subdir = os.path.join(d, "proj3")
            os.makedirs(subdir)
            with open(os.path.join(subdir, ".auto_linter.json"), "w") as f:
                f.write("{}")
            with open(os.path.join(subdir, "auto_linter.config.yaml"), "w") as f:
                f.write("{}")
            result = find_projects(d)
            assert len(result) == 1
        finally:
            shutil.rmtree(d)

    def test_custom_config_name(self):
        d = tempfile.mkdtemp()
        try:
            with open(os.path.join(d, "my_config.json"), "w") as f:
                f.write("{}")
            result = find_projects(d, config_name="my_config.json")
            assert len(result) == 1
        finally:
            shutil.rmtree(d)

    def test_nested_directories(self):
        d = tempfile.mkdtemp()
        try:
            nested = os.path.join(d, "a", "b", "c")
            os.makedirs(nested)
            with open(os.path.join(nested, ".auto_linter.json"), "w") as f:
                f.write("{}")
            result = find_projects(d)
            assert len(result) == 1
        finally:
            shutil.rmtree(d)


# ── load_multi_project_config ─────────────────────────────────────

class TestLoadMultiProjectConfig:
    def test_missing_file(self):
        result = load_multi_project_config(Path("/nonexistent/config.json"))
        assert result == []

    def test_valid_config(self):
        d = tempfile.mkdtemp()
        try:
            cfg = os.path.join(d, ".auto_linter.json")
            with open(cfg, "w") as f:
                json.dump({"multi_project_paths": ["/a", "/b"]}, f)
            result = load_multi_project_config(Path(cfg))
            assert result == ["/a", "/b"]
        finally:
            shutil.rmtree(d)


# ── aggregate_results ────────────────────────────────────────────

class TestAggregateResults:
    def test_empty_list(self):
        orch = MultiProjectOrchestrator(MagicMock())
        ar = orch.aggregate_results([])
        assert ar.total_projects == 0
        assert ar.average_score == 0.0

    def test_all_passing(self):
        orch = MultiProjectOrchestrator(MagicMock())
        projects = [
            ProjectResult(path="/a", score=90.0, is_passing=True),
            ProjectResult(path="/b", score=80.0, is_passing=True),
        ]
        ar = orch.aggregate_results(projects)
        assert ar.total_projects == 2
        assert ar.passing_projects == 2
        assert ar.failing_projects == 0
        assert ar.average_score == 85.0

    def test_all_failing(self):
        orch = MultiProjectOrchestrator(MagicMock())
        projects = [
            ProjectResult(path="/a", score=0.0, is_passing=False),
            ProjectResult(path="/b", score=0.0, is_passing=False),
        ]
        ar = orch.aggregate_results(projects)
        assert ar.passing_projects == 0
        assert ar.failing_projects == 2
        assert ar.average_score == 0.0

    def test_mixed_results(self):
        orch = MultiProjectOrchestrator(MagicMock())
        projects = [
            ProjectResult(path="/a", score=100.0, is_passing=True),
            ProjectResult(path="/b", score=50.0, is_passing=False),
        ]
        ar = orch.aggregate_results(projects)
        assert ar.passing_projects == 1
        assert ar.failing_projects == 1
        assert ar.average_score == 75.0

    def test_zero_scores_excluded_from_average(self):
        orch = MultiProjectOrchestrator(MagicMock())
        projects = [
            ProjectResult(path="/a", score=80.0, is_passing=True),
            ProjectResult(path="/b", score=0.0, is_passing=False),
        ]
        ar = orch.aggregate_results(projects)
        assert ar.average_score == 80.0


# ── analyze_project tests ───────────────────────────────────────────

class TestAnalyzeProject:
    @pytest.mark.asyncio
    async def test_analyze_project_success(self):
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(return_value=MagicMock())
        mock_use_case.to_dict = MagicMock(return_value={
            "score": 85.0,
            "is_passing": True,
            "summary": "ok",
            "ruff": [],
            "mypy": [],
        })
        orch = MultiProjectOrchestrator(mock_use_case)
        result = await orch.analyze_project(Path("/tmp/test"))
        assert result.path == "/tmp/test"
        assert result.score == 85.0
        assert result.is_passing is True

    @pytest.mark.asyncio
    async def test_analyze_project_exception(self):
        mock_use_case = MagicMock()
        mock_use_case.execute = AsyncMock(side_effect=Exception("lint failed"))
        orch = MultiProjectOrchestrator(mock_use_case)
        result = await orch.analyze_project(Path("/tmp/test"))
        assert result.path == "/tmp/test"
        assert result.score == 0.0
        assert result.is_passing is False
        assert result.error == "lint failed"


class TestScanProjects:
    @pytest.mark.asyncio
    async def test_scan_projects_empty(self):
        mock_use_case = MagicMock()
        orch = MultiProjectOrchestrator(mock_use_case)
        with patch("agent.multi_project_orchestrator.find_projects", return_value=[]):
            result = await orch.scan_all_projects(Path("/tmp"))
            assert result.total_projects == 0

    @pytest.mark.asyncio
    async def test_scan_projects_single(self):
        mock_use_case = MagicMock()
        orch = MultiProjectOrchestrator(mock_use_case)
        mock_result = ProjectResult(path="/a", score=85.0, is_passing=True)
        with patch("agent.multi_project_orchestrator.find_projects", return_value=[Path("/a")]):
            with patch.object(orch, "analyze_project", new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = mock_result
                result = await orch.scan_all_projects(Path("/tmp"))
                assert result.total_projects == 1
                assert result.passing_projects == 1
                assert result.failing_projects == 0

    @pytest.mark.asyncio
    async def test_scan_projects_multiple(self):
        mock_use_case = MagicMock()
        orch = MultiProjectOrchestrator(mock_use_case)
        results = [
            ProjectResult(path="/a", score=100.0, is_passing=True),
            ProjectResult(path="/b", score=0.0, is_passing=False),
        ]
        with patch("agent.multi_project_orchestrator.find_projects", return_value=[Path("/a"), Path("/b")]):
            with patch.object(orch, "analyze_project", new_callable=AsyncMock) as mock_analyze:
                mock_analyze.side_effect = results
                result = await orch.scan_all_projects(Path("/tmp"))
                assert result.total_projects == 2
                assert result.passing_projects == 1
                assert result.failing_projects == 1
