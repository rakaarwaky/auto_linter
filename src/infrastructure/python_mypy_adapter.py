"""MyPy adapter for Python type checking."""
import logging
import os
import re
import subprocess
from typing import List, Optional

from taxonomy.lint_result_models import ILinterAdapter, LintResult, Severity
from taxonomy.relative_path_resolver import normalize_path

logger = logging.getLogger("mcp.adapters.mypy")


class MyPyAdapter(ILinterAdapter):
    """Adapter for MyPy type checker."""

    def __init__(self, bin_path: Optional[str] = None):
        self.bin_path = bin_path

    def name(self) -> str:
        return "mypy"

    def scan(self, path: str) -> List[LintResult]:
        path = normalize_path(path)
        results: List[LintResult] = []
        try:
            abs_path = os.path.abspath(path)
            executable = self._resolve_executable("mypy")

            cmd = [executable, abs_path, "--ignore-missing-imports", "--no-error-summary"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=os.getcwd(), timeout=120)
            output = result.stdout + result.stderr

            pattern = re.compile(r"^([^:]+):(\d+):(?:(\d+):)?\s+(\w+):\s+(.*)$")

            for line in output.splitlines():
                match = pattern.match(line.strip())
                if match:
                    filename, line_num, col_num, msg_type, msg = match.groups()
                    severity = self._map_severity(msg_type)

                    if not os.path.isabs(filename):
                        base_dir = (
                            os.path.dirname(os.path.abspath(path))
                            if os.path.isfile(path)
                            else os.path.abspath(path)
                        )
                        filename = os.path.join(base_dir, filename)
                    elif not os.path.exists(filename):
                        filename = os.path.abspath(filename)

                    results.append(LintResult(
                        file=filename,
                        line=int(line_num),
                        column=int(col_num) if col_num and col_num.isdigit() else 0,
                        code="mypy",
                        message=msg,
                        source="mypy",
                        severity=severity,
                    ))

        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"Error running MyPy: {e}")

        return results

    def apply_fix(self, path: str) -> bool:
        return False

    def _resolve_executable(self, name: str) -> str:
        if isinstance(self.bin_path, str):
            return os.path.join(self.bin_path, name)
        return name

    def _map_severity(self, msg_type: str) -> Severity:
        if msg_type == "note":
            return Severity.INFO
        elif msg_type == "warning":
            return Severity.MEDIUM
        return Severity.HIGH
