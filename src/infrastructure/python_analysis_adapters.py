"""Adapters for Python: complexity, duplicates, trends, dependency scanning."""
import json
import logging
import os
import subprocess
from typing import List, Optional

from taxonomy.lint_result_models import ILinterAdapter, LintResult, Severity
from taxonomy.relative_path_resolver import normalize_path

logger = logging.getLogger("mcp.adapters.python")


class ComplexityAdapter(ILinterAdapter):
    """Adapter for Radon complexity checker."""

    def __init__(self, bin_path: Optional[str] = None):
        self.bin_path = bin_path

    def name(self) -> str:
        return "radon"

    def scan(self, path: str) -> List[LintResult]:
        path = normalize_path(path)
        results: List[LintResult] = []
        try:
            executable = "radon"
            if isinstance(self.bin_path, str):
                executable = os.path.join(self.bin_path, "radon")

            cmd = [executable, "cc", os.path.abspath(path), "-s", "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if not result.stdout.strip():
                return []

            data = json.loads(result.stdout)
            for filename, issues in data.items():
                for issue in issues:
                    if issue.get("complexity", 0) > 10:
                        results.append(LintResult(
                            file=filename,
                            line=issue["lineno"],
                            column=issue.get("col_offset", 0),
                            code="complexity",
                            message=f"High complexity ({issue['complexity']}) in {issue['name']}",
                            source="radon",
                            severity=Severity.MEDIUM,
                        ))
        except Exception as e:
            logger.error(f"Error running Radon: {e}")
        return results

    def apply_fix(self, path: str) -> bool:
        return False


class DuplicateAdapter(ILinterAdapter):
    """Adapter for duplicate code detection."""

    def __init__(self, bin_path: Optional[str] = None):
        self.bin_path = bin_path

    def name(self) -> str:
        return "duplicates"

    def scan(self, path: str) -> List[LintResult]:
        path = normalize_path(path)
        results: List[LintResult] = []
        try:
            abs_path = os.path.abspath(path)
            if os.path.isfile(abs_path):
                self._check_file(abs_path, results)
            elif os.path.isdir(abs_path):
                for dirpath, _, filenames in os.walk(abs_path):
                    if "__pycache__" in dirpath or ".venv" in dirpath:
                        continue
                    for filename in filenames:
                        if filename.endswith(".py") or filename.endswith(".js") or filename.endswith(".ts"):
                            file_path = os.path.join(dirpath, filename)
                            self._check_file(file_path, results)
        except Exception:
            pass
        return results

    def _check_file(self, file_path: str, results: List[LintResult]):
        """Helper to check a single file's length."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if len(lines) > 500:
                    results.append(LintResult(
                        file=file_path,
                        line=1,
                        column=0,
                        code="DUPE001",
                        message=f"File exceeds 500 lines ({len(lines)}); potential duplication or SRP violation.",
                        source="duplicates",
                        severity=Severity.LOW,
                    ))
        except (OSError, UnicodeDecodeError):
            pass

    def apply_fix(self, path: str) -> bool:
        return False


class TrendsAdapter(ILinterAdapter):
    """Adapter for quality trend tracking."""

    def __init__(self, history_file: str = ".auto_lint_history"):
        self.history_file = history_file

    def name(self) -> str:
        return "trends"

    def scan(self, path: str) -> List[LintResult]:
        results: List[LintResult] = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    history = [json.loads(line) for line in f]
                if len(history) > 1:
                    last_score = history[-1].get("score", 0)
                    prev_score = history[-2].get("score", 0)
                    if last_score < prev_score:
                        results.append(LintResult(
                            file="project",
                            line=0,
                            column=0,
                            code="TREND001",
                            message=f"Quality trend is negative: {prev_score} -> {last_score}",
                            source="trends",
                            severity=Severity.MEDIUM,
                        ))
            except Exception:
                pass
        return results

    def apply_fix(self, path: str) -> bool:
        return False


class DependencyAdapter(ILinterAdapter):
    """Adapter for dependency vulnerability scanning."""

    def __init__(self, bin_path: Optional[str] = None):
        self.bin_path = bin_path

    def name(self) -> str:
        return "pip-audit"

    def scan(self, path: str) -> List[LintResult]:
        path = normalize_path(path)
        results: List[LintResult] = []
        try:
            executable = "pip-audit"
            if isinstance(self.bin_path, str):
                executable = os.path.join(self.bin_path, "pip-audit")

            cmd = [executable, "-f", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if not result.stdout.strip():
                return []

            data = json.loads(result.stdout)
            for item in data.get("dependencies", []):
                for vuln in item.get("vulns", []):
                    results.append(LintResult(
                        file="requirements.txt",
                        line=0,
                        column=0,
                        code=vuln["id"],
                        message=f"Vulnerability in {item['name']} ({item['version']}): {vuln['fix_versions']}",
                        source="pip-audit",
                        severity=Severity.HIGH,
                    ))
        except Exception as e:
            logger.error(f"Error running pip-audit: {e}")
        return results

    def apply_fix(self, path: str) -> bool:
        return False
