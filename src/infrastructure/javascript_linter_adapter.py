import json
import logging
import os
import re
import subprocess
from typing import List
from taxonomy.lint_result_models import ILinterAdapter, LintResult, Severity
from infrastructure.path_normalization_util import normalize_path

logger = logging.getLogger("mcp.adapters.javascript")

class PrettierAdapter(ILinterAdapter):
    def name(self) -> str:
        return "prettier"

    def _resolve_filename(self, path: str) -> str:
        """Resolve filename with multiple fallbacks for phantom paths."""
        # 1. Try normalized path (PROJECT_ROOT replacement)
        norm_path = normalize_path(path)
        if norm_path and os.path.exists(norm_path):
            return norm_path
            
        # 2. Try absolute path of original
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return abs_path
            
        # 3. Last resort: Return normalized path if it exists now (secondary check for some test environments)
        if norm_path and os.path.exists(norm_path):
            return norm_path
            
        return norm_path or abs_path

    def scan(self, path: str) -> List[LintResult]:
        if os.path.isfile(path) and not path.endswith(
            (".ts", ".tsx", ".js", ".jsx", ".json", ".css", ".md", ".yml", ".yaml")
        ):
            return []

        results = []
        try:
            abs_path = os.path.abspath(path)
            cmd = ["npx", "prettier", "--check", abs_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode == 0:
                return []

            combined_output = (result.stdout + result.stderr).strip()

            if "[warn]" in combined_output:
                filename = self._resolve_filename(path)
                results.append(
                    LintResult(
                        file=filename,
                        line=0,
                        column=0,
                        code="formatting",
                        message="Code style issues found. Run Prettier to fix.",
                        source="prettier",
                        severity=Severity.LOW,
                    )
                )
        except Exception as e:
            logger.error(f"Error running Prettier: {e}")

        return results

    def apply_fix(self, path: str) -> bool:
        try:
            abs_path = os.path.abspath(path)
            cmd = ["npx", "prettier", "--write", abs_path]
            subprocess.run(cmd, capture_output=True, text=True, check=False)
            return True
        except Exception as e:
            logger.error(f"Error applying Prettier fixes: {e}")
            return False

class TSCAdapter(ILinterAdapter):
    def name(self) -> str:
        return "tsc"

    def _resolve_filename(self, filename: str, scan_path: str) -> str:
        """Resolve filename with multiple fallbacks for phantom paths."""
        # Ensure absolute path first
        if not os.path.isabs(filename):
            base_dir = os.path.dirname(os.path.abspath(scan_path)) if os.path.isfile(scan_path) else os.path.abspath(scan_path)
            filename = os.path.join(base_dir, filename)

        # 1. Try normalized path
        norm_path = normalize_path(filename)
        if norm_path and os.path.exists(norm_path):
            return norm_path
            
        # 2. Try absolute path
        abs_path = os.path.abspath(filename)
        if os.path.exists(abs_path):
            return abs_path
            
        # 3. Last resort
        if norm_path and os.path.exists(norm_path):
            return norm_path
            
        return norm_path or abs_path

    def scan(self, path: str) -> List[LintResult]:
        if os.path.isfile(path) and not path.endswith((".ts", ".tsx")):
            return []

        results = []
        try:
            # We must run npx tsc in the directory where tsconfig.json is
            # usually the root or the parent of path
            abs_path = os.path.abspath(path)
            cmd = ["npx", "tsc", "--noEmit", "--pretty", "false"]
            if abs_path != "." and abs_path != "./":
                cmd.append(abs_path)

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = result.stdout + result.stderr

            pattern1 = re.compile(r"^([^(]+)\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.*)$")
            pattern2 = re.compile(r"^([^:]+):(\d+):(\d+)\s+-\s+error\s+(TS\d+):\s+(.*)$")

            for line in output.splitlines():
                line = line.strip()
                match = pattern1.match(line) or pattern2.match(line)
                if match:
                    filename, line_num, col_num, code, msg = match.groups()
                    
                    filename = self._resolve_filename(filename, abs_path)

                    results.append(
                        LintResult(
                            file=filename,
                            line=int(line_num),
                            column=int(col_num),
                            code=code,
                            message=msg,
                            source="tsc",
                            severity=Severity.HIGH,
                        )
                    )
        except Exception as e:
            logger.error(f"Error running TSC: {e}")

        return results

    def apply_fix(self, path: str) -> bool:
        return False

class ESLintAdapter(ILinterAdapter):
    def name(self) -> str:
        return "eslint"

    def _resolve_filename(self, filename: str) -> str:
        """Resolve filename with multiple fallbacks for phantom paths."""
        # 1. Try normalized path
        norm_path = normalize_path(filename)
        if norm_path and os.path.exists(norm_path):
            return norm_path
            
        # 2. Try absolute path
        abs_path = os.path.abspath(filename)
        if os.path.exists(abs_path):
            return abs_path
            
        # 3. Last resort
        if norm_path and os.path.exists(norm_path):
            return norm_path
            
        return norm_path or abs_path

    def scan(self, path: str) -> List[LintResult]:
        if os.path.isfile(path) and not path.endswith((".ts", ".tsx", ".js", ".jsx")):
            return []

        results = []
        try:
            abs_path = os.path.abspath(path)
            cmd = ["npx", "eslint", abs_path, "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if not result.stdout.strip():
                return []

            data = json.loads(result.stdout)
            for file_data in data:
                filename = file_data["filePath"]
                filename = self._resolve_filename(filename)

                for msg in file_data["messages"]:
                    results.append(
                        LintResult(
                            file=filename,
                            line=msg.get("line", 0),
                            column=msg.get("column", 0),
                            code=msg.get("ruleId", "ESLINT"),
                            message=msg["message"],
                            source="eslint",
                            severity=Severity.HIGH if msg["severity"] == 2 else Severity.MEDIUM,
                        )
                    )
        except Exception as e:
            logger.error(f"Error running ESLint: {e}")

        return results

    def apply_fix(self, path: str) -> bool:
        try:
            abs_path = os.path.abspath(path)
            cmd = ["npx", "eslint", abs_path, "--fix"]
            subprocess.run(cmd, capture_output=True, text=True, check=False)
            return True
        except Exception as e:
            logger.error(f"Error applying ESLint fixes: {e}")
            return False
