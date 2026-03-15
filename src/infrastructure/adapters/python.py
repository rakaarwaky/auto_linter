import json
import logging
import os
import re
import subprocess
from typing import List, Optional
from ...core._taxonomy.models import ILinterAdapter, LintResult, Severity
from ...core._taxonomy.path_utils import normalize_path

logger = logging.getLogger("mcp.auto_linter.adapters.python")

class RuffAdapter(ILinterAdapter):
    def __init__(self, bin_path: Optional[str] = None):
        self.bin_path = bin_path

    def name(self) -> str:
        return "ruff"

    def scan(self, path: str) -> List[LintResult]:
        # Normalize path before scanning
        path = normalize_path(path)

        results = []
        try:
            abs_path = os.path.abspath(path)
            executable = "ruff"
            bp = self.bin_path
            if isinstance(bp, str):
                executable = os.path.join(bp, "ruff")
            
            cmd = [executable, "check", abs_path, "--output-format=json", "--exit-zero", "--no-cache"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=os.getcwd())
            
            data = []
            # Filter out Ruff's "No such file or directory" pseudo-errors for phantom paths
            # This happens in some environments when Ruff uses a stale cache or has path resolution mismatches
            stdout_clean = result.stdout.strip()
            if not stdout_clean:
                return []

            try:
                data = json.loads(stdout_clean)
            except json.JSONDecodeError:
                if "[" in stdout_clean:
                    try:
                        # Use split instead of find to satisfy Pyre string indexing quirks
                        parts = stdout_clean.split("[", 1)
                        if len(parts) > 1:
                            valid_json = "[" + str(parts[1])
                            data = json.loads(valid_json)
                        else:
                            return []  # pragma: no cover
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode Ruff output: {stdout_clean}")
                        return []
                else:
                    return []

            if "No such file or directory" in stdout_clean and "E902" in stdout_clean:
                real_errors = []
                for item in data:
                    filename = item.get("filename", "")
                    # Handle potential phantom path in environment
                    if item.get("code") == "E902" and "/home/raka/src/" in filename:
                         actual_path = filename.replace("/home/raka/src/", "/persistent/home/raka/mcp-servers/auto_linter/src/").replace("//", "/")
                         if os.path.exists(actual_path):
                             continue
                         else:
                             continue
                    elif item.get("code") == "E902" and not os.path.exists(filename):
                        continue
                    real_errors.append(item)
                
                if not real_errors:
                    return []
                data = real_errors

            for item in data:
                code = item.get("code", "")
                severity = Severity.MEDIUM

                if code.startswith("F") or code.startswith("E9"):
                    severity = Severity.HIGH
                elif code.startswith("W"):
                    severity = Severity.LOW

                # Ensure absolute path
                filename = item["filename"]
                if not os.path.isabs(filename):
                     # If we scanned with a relative path, Ruff might return relative to CWD
                     # We want it relative to our project root or the requested path's base
                     base_dir = os.path.dirname(os.path.abspath(path)) if os.path.isfile(path) else os.path.abspath(path)
                     
                     possible_path = os.path.join(base_dir, filename)
                     if os.path.exists(possible_path):
                         filename = possible_path
                     elif os.path.exists(os.path.abspath(filename)):
                         filename = os.path.abspath(filename)
                     
                # Final check: if it still has /home/raka/src/ but /persistent/ exists
                if "/home/raka/src/" in filename:
                    alt_path = filename.replace("/home/raka/src/", "/persistent/home/raka/mcp-servers/auto_linter/src/").replace("//", "/")
                    if os.path.exists(alt_path):
                        filename = alt_path
                    else:
                        # Emergency fallback for this specific environment mismatch
                        # Even if it doesn't exist, we map it to the project path to avoid referencing phantoms
                        suffix = filename.split("/home/raka/src/")[-1]
                        filename = os.path.join("/persistent/home/raka/mcp-servers/auto_linter/src/", suffix).replace("//", "/")

                lint_result = LintResult(
                    file=filename,
                    line=item["location"]["row"],
                    column=item["location"]["column"],
                    code=code,
                    message=item["message"],
                    source="ruff",
                    severity=severity,
                )
                results.append(lint_result)

        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"Error running Ruff: {e}")

        return results

class MyPyAdapter(ILinterAdapter):
    def __init__(self, bin_path: Optional[str] = None):
        self.bin_path = bin_path

    def name(self) -> str:
        return "mypy"

    def scan(self, path: str) -> List[LintResult]:
        # Normalize path before scanning
        path = normalize_path(path)

        results = []
        try:
            abs_path = os.path.abspath(path)
            executable = "mypy"
            bp = self.bin_path
            if isinstance(bp, str):
                executable = os.path.join(bp, "mypy")
                
            cmd = [executable, abs_path, "--ignore-missing-imports", "--no-error-summary"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=os.getcwd())
            output = result.stdout + result.stderr

            pattern = re.compile(r"^([^:]+):(\d+):(?:(\d+):)?\s+(\w+):\s+(.*)$")

            for line in output.splitlines():
                match = pattern.match(line.strip())
                if match:
                    filename, line_num, col_num, msg_type, msg = match.groups()

                    severity = Severity.HIGH
                    if msg_type == "note":
                        severity = Severity.INFO
                    elif msg_type == "warning":
                        severity = Severity.MEDIUM

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
                            column=int(col_num) if col_num and col_num.isdigit() else 0,
                            code="mypy",
                            message=msg,
                            source="mypy",
                            severity=severity,
                        )
                    )

        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"Error running MyPy: {e}")

        return results
