"""Ruff adapter for Python linting."""
import json
import logging
import os
import subprocess
from typing import List, Optional

from taxonomy.lint_result_models import ILinterAdapter, LintResult, Severity
from taxonomy.relative_path_resolver import normalize_path

logger = logging.getLogger("mcp.adapters.ruff")


class RuffAdapter(ILinterAdapter):
    """Adapter for Ruff linter."""

    def __init__(self, bin_path: Optional[str] = None):
        self.bin_path = bin_path

    def name(self) -> str:
        return "ruff"

    def scan(self, path: str) -> List[LintResult]:
        path = normalize_path(path)
        results: List[LintResult] = []
        try:
            abs_path = os.path.abspath(path)
            executable = self._resolve_executable("ruff")

            cmd = [executable, "check", abs_path, "--output-format=json", "--exit-zero", "--no-cache"]
            # DEBUG: click.echo(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=os.getcwd(), timeout=60)

            if result.stderr:
                logger.error(f"Ruff Stderr: {result.stderr}")

            stdout_clean = result.stdout.strip()
            if not stdout_clean:
                # logger.info("Ruff returned empty stdout")
                return []

            data = self._parse_json_output(stdout_clean)
            if not data:
                # logger.info("Ruff returned no valid JSON data")
                return []

            data = self._filter_phantom_errors(data)

            for item in data:
                results.append(self._to_lint_result(item, path))

        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"Error running Ruff: {e}")

        return results

    def apply_fix(self, path: str) -> bool:
        path = normalize_path(path)
        try:
            executable = self._resolve_executable("ruff")
            cmd = [executable, "check", path, "--fix", "--exit-zero"]
            subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=os.getcwd(), timeout=60)
            return True
        except Exception as e:
            logger.error(f"Error applying Ruff fixes: {e}")
            return False

    def _resolve_executable(self, name: str) -> str:
        if isinstance(self.bin_path, str):
            return os.path.join(self.bin_path, name)
        return name

    def _parse_json_output(self, stdout: str) -> List[dict]:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            if "[" in stdout:
                try:
                    parts = stdout.split("[", 1)
                    if len(parts) > 1:
                        return json.loads("[" + parts[1])
                except json.JSONDecodeError:
                    pass
            return []

    def _filter_phantom_errors(self, data: List[dict]) -> List[dict]:
        """Filter out E902 errors for non-existent files."""
        real_errors: List[dict] = []
        for item in data:
            if item.get("code") == "E902":
                filename = item.get("filename", "")
                if not os.path.exists(filename):
                    continue
            real_errors.append(item)
        return real_errors

    def _to_lint_result(self, item: dict, scan_path: str) -> LintResult:
        code = item.get("code", "")
        severity = Severity.MEDIUM
        if code.startswith("F") or code.startswith("E9"):
            severity = Severity.HIGH
        elif code.startswith("W"):
            severity = Severity.LOW

        filename = self._resolve_filename(item["filename"], scan_path)

        return LintResult(
            file=filename,
            line=item["location"]["row"],
            column=item["location"]["column"],
            code=code,
            message=item["message"],
            source="ruff",
            severity=severity,
        )

    def _resolve_filename(self, filename: str, scan_path: str) -> str:
        """Ensure we return an absolute path."""
        if not os.path.isabs(filename):
            base_dir = (
                os.path.dirname(os.path.abspath(scan_path))
                if os.path.isfile(scan_path)
                else os.path.abspath(scan_path)
            )
            possible_path = os.path.join(base_dir, filename)
            if os.path.exists(possible_path):
                return possible_path
            elif os.path.exists(os.path.abspath(filename)):
                return os.path.abspath(filename)
        return filename
