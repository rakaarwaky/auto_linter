import os
import re
import subprocess
import json
from src.core._taxonomy.models import ILinterAdapter, GovernanceReport, ISemanticTracer
from typing import List, Dict, Any, Optional
class RunAnalysisUseCase:
    """Orchestrates the multi-linter analysis (Capability)."""

    def __init__(self, adapters: List[ILinterAdapter], tracers: Optional[Dict[str, ISemanticTracer]] = None):
        self.adapters = adapters
        self.tracers = tracers or {}

    async def execute(self, path: str) -> GovernanceReport:
        report = GovernanceReport()
        root_dir = path if os.path.exists(path) and os.path.isdir(path) else os.path.dirname(path)

        for adapter in self.adapters:
            try:
                results = adapter.scan(path)
                for res in results:
                    report.add_result(res)
            except Exception as e:
                # In a real Agentic structure, we'd log this to an Infrastructure logger
                print(f"Error in adapter {adapter.name()}: {e}")

        # Pass 2: Enrichment (Diagnostic Context Phase)
        for res in report.results:
            tracer = self.tracers.get("python") if res.file.endswith(".py") else self.tracers.get("js")
            if not tracer:
                continue

            # Always extract structural scope
            if hasattr(tracer, "show_enclosing_scope"):
                scope = tracer.show_enclosing_scope(res.file, res.line)
                if scope:
                    res.enclosing_scope = scope

            # Check for possible missing argument or undefined errors (call chains)
            if "missing" in res.message.lower() or "argument" in res.message.lower():
                # Attempt to extract function name
                match = re.search(r"function\s+[`']?([a-zA-Z0-9_]+)[`']?", res.message)
                if match:
                    func_name = match.group(1)
                    if hasattr(tracer, "trace_call_chain"):
                        callers = tracer.trace_call_chain(root_dir, func_name)
                        if callers:
                            res.related_locations.extend([f"Caller: {c}" for c in callers[:5]])

            # Check for unused variable or data mutations
            if "unused" in res.message.lower() or "assign" in res.message.lower():
                # Attempt to extract variable name
                match = re.search(r"[`'](.*?)[`']", res.message)
                if match:
                    var_name = match.group(1)
                    if hasattr(tracer, "find_flow"):
                        flows = tracer.find_flow(res.file, var_name, res.line)
                        if flows:
                            res.related_locations.extend(flows)

        return report

    def to_dict(self, report: GovernanceReport) -> dict:
        """Converts report to standardized JSON output."""
        output: Dict[str, Any] = {
            "governance": [],
            "ruff": [],
            "mypy": [],
            "prettier": [],
            "eslint": [],
            "tsc": [],
            "summary": {},
        }

        for res in report.results:
            source = res.source
            if source == "summary":
                source = "governance" # Redirect summary source to governance
            
            if source not in output or not isinstance(output[source], list):
                output[source] = []

            output[source].append(
                {
                    "file": res.file,
                    "line": res.line,
                    "code": res.code,
                    "message": res.message,
                    "severity": res.severity.value,
                    "column": res.column,
                    "enclosing_scope": res.enclosing_scope,
                    "related_locations": res.related_locations,
                }
            )

        output["summary"] = {k: len(v) for k, v in output.items() if isinstance(v, list)}
        output["score"] = report.score
        output["is_passing"] = report.is_passing
        return output

class ApplyFixesUseCase:
    """Orchestrates automatic fixes (Capability)."""

    def __init__(self, venv_bin: str, tracers: Optional[Dict[str, ISemanticTracer]] = None):
        self.venv_bin = venv_bin
        self.tracers = tracers or {}

    async def execute(self, path: str) -> str:
        root_dir = path if os.path.exists(path) and os.path.isdir(path) else os.path.dirname(path)
        
        output_log = ""
        renamed_modifications: int = 0
        try:
            # Step 1: Pre-fix semantic renaming logic
            ruff_path = os.path.join(self.venv_bin, "ruff")
            check_cmd = [ruff_path, "check", path, "--output-format=json"]
            check_proc = subprocess.run(check_cmd, capture_output=True, text=True, check=False)
            
            try:
                if check_proc.stdout.strip():
                    results = json.loads(check_proc.stdout)
                    renamed_modifications = 0
                    tracer = self.tracers.get("python")
                    
                    if tracer:
                        for r in results:
                            code = r.get("code")
                            msg = r.get("message", "")
                            
                            old_name = None
                            new_name = None
                            
                            # N802, N803, N806: Function/Argument/Variable should be lowercase (snake_case)
                            if code in ["N802", "N803", "N806"]:
                                match = re.search(r"[`'](.*?)[`']", msg)
                                if match:
                                    old_name = match.group(1)
                                    new_name = tracer.get_variant_dict(old_name)["snake_case"]
                            # N801: Class names should use CapWords (PascalCase)
                            elif code == "N801":
                                match = re.search(r"[`'](.*?)[`']", msg)
                                if match:
                                    old_name = match.group(1)
                                    new_name = tracer.get_variant_dict(old_name)["pascal_case"]
                                    
                            if old_name and new_name and old_name != new_name:
                                mods = tracer.project_wide_rename(root_dir, old_name, new_name)
                                if isinstance(mods, int) and mods > 0:
                                    renamed_modifications += mods
                                    msg_line = f"Semantic Rename: Changed '{old_name}' -> '{new_name}' across {mods} files.\n"
                                    output_log = str(output_log or "") + msg_line
            except json.JSONDecodeError:
                pass
                
            # Step 2: Ruff standard auto-fixes
            cmd = [ruff_path, "check", path, "--fix", "--exit-zero"]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output_log = output_log + f"Ruff Fix Output:\n{proc.stdout}\n{proc.stderr}"

            js_fix_output = ""
            if path.endswith((".ts", ".tsx", ".js", ".jsx", ".json", ".css", ".md")):
                if path.endswith((".ts", ".tsx", ".js", ".jsx")):
                    eslint_cmd = ["npx", "eslint", path, "--fix"]
                    proc_js = subprocess.run(eslint_cmd, capture_output=True, text=True, check=False)
                    js_fix_output += f"\nESLint Fix Output:\n{proc_js.stdout}\n{proc_js.stderr}"

                prettier_cmd = ["npx", "prettier", "--write", path]
                proc_prettier = subprocess.run(prettier_cmd, capture_output=True, text=True, check=False)
                js_fix_output += f"\nPrettier Fix Output:\n{proc_prettier.stdout}\n{proc_prettier.stderr}"

            output_log += js_fix_output
            return output_log
        except FileNotFoundError:
            return "Error: Linter executable not found."
