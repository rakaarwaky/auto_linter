import os
import re
from taxonomy.lint_result_models import ILinterAdapter, GovernanceReport, ISemanticTracer
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

    def __init__(self, adapters: List[ILinterAdapter], tracers: Optional[Dict[str, ISemanticTracer]] = None):
        self.adapters = adapters
        self.tracers = tracers or {}

    async def execute(self, path: str) -> str:
        root_dir = path if os.path.exists(path) and os.path.isdir(path) else os.path.dirname(path)
        
        output_log = ""
        renamed_modifications: int = 0
        try:
            # Step 1: Pre-fix semantic renaming logic (Python specific for now)
            tracer = self.tracers.get("python")
            if tracer and path.endswith(".py"):
                # We still use ruff here to find naming violations
                # In a more generic setup, this might be its own adapter or use case
                # For now, we'll keep the semantic rename logic tied to Python
                
                # Find ruff path from adapters if possible, or assume it's in env
                ruff_adapter = next((a for a in self.adapters if a.name() == "ruff"), None)
                if ruff_adapter:
                    # We reuse the scan to find naming violations
                    results = ruff_adapter.scan(path)
                    for r in results:
                        if r.code in ["N802", "N803", "N806", "N801"]:
                            old_name = None
                            new_name = None
                            
                            match = re.search(r"[`'](.*?)[`']", r.message)
                            if match:
                                old_name = match.group(1)
                                if r.code == "N801":
                                    new_name = tracer.get_variant_dict(old_name)["pascal_case"]
                                else:
                                    new_name = tracer.get_variant_dict(old_name)["snake_case"]
                                    
                            if old_name and new_name and old_name != new_name:
                                mods = tracer.project_wide_rename(root_dir, old_name, new_name)
                                if isinstance(mods, int) and mods > 0:
                                    renamed_modifications += mods
                                    output_log += f"Semantic Rename: Changed '{old_name}' -> '{new_name}' across {mods} files.\n"

            # Step 2: Apply fixes via adapters
            for adapter in self.adapters:
                # We skip the governance adapter since it doesn't "fix" things
                if adapter.name() == "governance":
                    continue
                
                if adapter.apply_fix(path):
                    output_log += f"[{adapter.name()}] Applied automatic fixes.\n"
                else:
                    output_log += f"[{adapter.name()}] No fixes applied or not supported.\n"

            return output_log
        except Exception as e:
            return f"Error during fix application: {e}"
