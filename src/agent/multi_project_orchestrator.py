"""Multi-project orchestration — Agent responsibility.

Coordinates scanning across multiple project directories.
Uses taxonomy VOs for shared language. Never defines its own types.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional

from taxonomy.multi_project_vo import ProjectResult, AggregatedResults


def find_projects(root: str | Path, config_name: str = ".auto_linter.json") -> list[Path]:
    """Find all projects with auto-linter configs."""
    root = Path(root)
    projects: list[Path] = []
    for config_file in root.rglob(config_name):
        projects.append(config_file.parent)
    for config_file in root.rglob("auto_linter.config.yaml"):
        if config_file.parent not in projects:
            projects.append(config_file.parent)
    return projects


def load_multi_project_config(path: Optional[Path] = None) -> List[str]:
    """Load list of project paths from config."""
    from pathlib import Path as P
    import json
    config_path = path or P.cwd() / ".auto_linter.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text())
            return data.get("multi_project_paths", [])
        except Exception:
            pass
    return []


class MultiProjectOrchestrator:
    """Orchestrates multi-project scans.

    Agent coordinates. Infrastructure adapts. Capabilities think.
    """

    def __init__(self, analysis_use_case):
        self.analysis_use_case = analysis_use_case

    async def analyze_project(self, path: Path) -> ProjectResult:
        """Analyze a single project."""
        try:
            report = await self.analysis_use_case.execute(str(path))
            data = self.analysis_use_case.to_dict(report)
            issues = []
            for source, results in data.items():
                if source in ["score", "summary", "is_passing", "governance"]:
                    continue
                if isinstance(results, list):
                    issues.extend(results)
            return ProjectResult(
                path=str(path),
                score=data.get("score", 0.0),
                is_passing=data.get("is_passing", True),
                issues=issues,
                adapters=list(data.keys() - {"score", "summary", "is_passing", "governance"}),
            )
        except Exception as e:
            return ProjectResult(
                path=str(path),
                score=0.0,
                is_passing=False,
                issues=[],
                adapters=[],
                error=str(e),
            )

    async def scan_all_projects(
        self,
        root: str | Path | list[str | Path],
        max_concurrency: int = 10,
    ) -> AggregatedResults:
        """Scan all projects in a workspace or a specific list of projects."""
        if isinstance(root, list):
            projects = [Path(p) for p in root]
        else:
            projects = find_projects(root)
            
        if not projects:
            return AggregatedResults()
        semaphore = asyncio.Semaphore(max_concurrency)

        async def limited_analyze(p: Path) -> ProjectResult:
            async with semaphore:
                return await self.analyze_project(p)

        results = await asyncio.gather(*[limited_analyze(p) for p in projects])
        return self.aggregate_results(list(results))

    def aggregate_results(self, projects: list[ProjectResult]) -> AggregatedResults:
        """Aggregate results from multiple projects."""
        passing = [p for p in projects if p.is_passing]
        scores = [p.score for p in projects if p.score > 0]
        return AggregatedResults(
            projects=projects,
            total_projects=len(projects),
            passing_projects=len(passing),
            failing_projects=len(projects) - len(passing),
            average_score=sum(scores) / len(scores) if scores else 0.0,
        )
