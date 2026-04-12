"""Multi-project value objects — shared language for cross-project analysis."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProjectResult:
    """Result from a single project scan."""
    path: str
    score: float
    is_passing: bool
    issues: list[dict] = field(default_factory=list)
    adapters: list[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class AggregatedResults:
    """Aggregated results from multiple projects."""
    projects: list[ProjectResult] = field(default_factory=list)
    total_projects: int = 0
    passing_projects: int = 0
    failing_projects: int = 0
    average_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "projects": [
                {
                    "path": p.path,
                    "score": p.score,
                    "is_passing": p.is_passing,
                    "issues_count": len(p.issues),
                    "adapters": p.adapters,
                    "error": p.error,
                }
                for p in self.projects
            ],
            "summary": {
                "total_projects": self.total_projects,
                "passing_projects": self.passing_projects,
                "failing_projects": self.failing_projects,
                "average_score": self.average_score,
            },
        }

    def to_text(self) -> str:
        lines = ["Multi-Project Scan Results", "=" * 40]
        for p in self.projects:
            if p.error:
                lines.append(f" ERROR {p.path}: {p.error}")
            else:
                status = " PASS" if p.is_passing else " FAIL"
                lines.append(f"{status} {p.path} (score: {p.score:.1f})")
        summary = self.to_dict()["summary"]
        lines.extend([
            "",
            "Summary:",
            f"  Total: {summary['total_projects']}",
            f"  Passing: {summary['passing_projects']}",
            f"  Failing: {summary['failing_projects']}",
            f"  Average Score: {summary['average_score']:.1f}",
        ])
        return "\n".join(lines)
