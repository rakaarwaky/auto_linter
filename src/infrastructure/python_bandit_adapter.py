"""Bandit adapter for Python security scanning."""
import json
import logging
import os
import subprocess
from typing import List, Optional

from taxonomy.lint_result_models import ILinterAdapter, LintResult, Severity
from taxonomy.relative_path_resolver import normalize_path

logger = logging.getLogger("mcp.adapters.bandit")


class BanditAdapter(ILinterAdapter):
    """Adapter for Bandit security scanner."""

    def __init__(self, bin_path: Optional[str] = None):
        self.bin_path = bin_path

    def name(self) -> str:
        return "bandit"

    def scan(self, path: str) -> List[LintResult]:
        path = normalize_path(path)
        results: List[LintResult] = []
        try:
            executable = "bandit"
            if isinstance(self.bin_path, str):
                executable = os.path.join(self.bin_path, "bandit")

            cmd = [executable, "-r", os.path.abspath(path), "-f", "json", "-q"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if not result.stdout.strip():
                return []

            data = json.loads(result.stdout)
            for item in data.get("results", []):
                severity = Severity.HIGH if item["issue_severity"] == "HIGH" else Severity.MEDIUM
                results.append(LintResult(
                    file=item["filename"],
                    line=item["line_number"],
                    column=0,
                    code=item["test_id"],
                    message=item["issue_text"],
                    source="bandit",
                    severity=severity,
                ))
        except Exception as e:
            logger.error(f"Error running Bandit: {e}")
        return results

    def apply_fix(self, path: str) -> bool:
        return False
