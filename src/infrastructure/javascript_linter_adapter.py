import json
import logging
import os
import re
import subprocess
from typing import List
from taxonomy.lint_result_models import ILinterAdapter, LintResult, Severity

logger = logging.getLogger("mcp.adapters.javascript")

class PrettierAdapter(ILinterAdapter):
    def name(self) -> str:
        return "prettier"

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
                # Ensure absolute path for Prettier
                filename = path
                if not os.path.isabs(filename):
                    filename = os.path.abspath(filename)
                
                # Normalize phantom environment paths
                if "/home/raka/src/" in filename:
                    alt_path = filename.replace("/home/raka/src/", "/persistent/home/raka/mcp-servers/auto_linter/src/").replace("//", "/")
                    if os.path.exists(alt_path):
                        filename = alt_path
                    elif not os.path.exists(filename):
                        suffix = filename.split("/home/raka/src/")[-1]
                        project_file = os.path.join("/persistent/home/raka/mcp-servers/auto_linter/src/", suffix).replace("//", "/")
                        if os.path.exists(project_file):
                            filename = project_file
                elif not os.path.exists(filename):
                    filename = os.path.abspath(filename)

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

    def scan(self, path: str) -> List[LintResult]:
        if os.path.isfile(path) and not path.endswith((".ts", ".tsx")):
            return []

        if "/home/raka/src/" in path:
            path = path.replace("/home/raka/src/", "/persistent/home/raka/mcp-servers/auto_linter/src/").replace("//", "/")

        results = []
        try:
            cmd = ["npx", "tsc", "--noEmit", "--pretty", "false"]
            if path != "." and path != "./":
                cmd.append(path)

            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = result.stdout + result.stderr

            pattern1 = re.compile(r"^([^(]+)\((\d+),(\d+)\):\s+error\s+(TS\d+):\s+(.*)$")
            pattern2 = re.compile(r"^([^:]+):(\d+):(\d+)\s+-\s+error\s+(TS\d+):\s+(.*)$")

            for line in output.splitlines():
                line = line.strip()
                match = pattern1.match(line) or pattern2.match(line)
                if match:
                    filename, line_num, col_num, code, msg = match.groups()
                    
                    # Ensure absolute path
                    if not os.path.isabs(filename):
                        base_dir = os.path.dirname(os.path.abspath(path)) if os.path.isfile(path) else os.path.abspath(path)
                        filename = os.path.join(base_dir, filename)
                    
                    # Normalize phantom environment paths
                    if "/home/raka/src/" in filename:
                        alt_path = filename.replace("/home/raka/src/", "/persistent/home/raka/mcp-servers/auto_linter/src/").replace("//", "/")
                        if os.path.exists(alt_path):
                            filename = alt_path
                        elif not os.path.exists(filename):
                            suffix = filename.split("/home/raka/src/")[-1]
                            project_file = os.path.join("/persistent/home/raka/mcp-servers/auto_linter/src/", suffix).replace("//", "/")
                            if os.path.exists(project_file):
                                filename = project_file
                    elif not os.path.exists(filename):
                        filename = os.path.abspath(filename)

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
        # TSC does not support auto-fixes
        return False

class ESLintAdapter(ILinterAdapter):
    def name(self) -> str:
        return "eslint"

    def scan(self, path: str) -> List[LintResult]:
        if os.path.isfile(path) and not path.endswith((".ts", ".tsx", ".js", ".jsx")):
            return []

        if "/home/raka/src/" in path:
            path = path.replace("/home/raka/src/", "/persistent/home/raka/mcp-servers/auto_linter/src/").replace("//", "/")

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
                
                # Ensure absolute path
                if not os.path.isabs(filename):
                    filename = os.path.abspath(filename)
                
                # Normalize phantom environment paths
                if "/home/raka/src/" in filename:
                    alt_path = filename.replace("/home/raka/src/", "/persistent/home/raka/mcp-servers/auto_linter/src/").replace("//", "/")
                    if os.path.exists(alt_path):
                        filename = alt_path
                    elif not os.path.exists(filename):
                        suffix = filename.split("/home/raka/src/")[-1]
                        project_file = os.path.join("/persistent/home/raka/mcp-servers/auto_linter/src/", suffix).replace("//", "/")
                        if os.path.exists(project_file):
                            filename = project_file
                elif not os.path.exists(filename):
                    filename = os.path.abspath(filename)

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
