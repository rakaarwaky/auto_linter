"""
GovernanceAdapter — Architectural Layer Rule Enforcer (Capability).

Enforces configurable architectural rules. The rules are defined in the 
configuration file (e.g., auto_linter.config.yaml).

Example AES Layer Rules (often used as defaults):
  surfaces      --> capabilities     (ALLOWED)
  surfaces      --> infrastructure   (FORBIDDEN)
  capabilities  --> infrastructure   (FORBIDDEN - use Taxonomy interfaces)
  capabilities  --> surfaces         (FORBIDDEN)
  infrastructure --> taxonomy        (ALLOWED)
  infrastructure --> surfaces        (FORBIDDEN)
  agent         --> *                (ALLOWED — wiring layer)

Detection strategy:
  1. Walk all Python files in the scanned path.
  2. For each file, use AST to extract all import targets.
  3. Apply rules from configuration to detect violations.
  4. Use PythonTracer.trace_call_chain to find cross-layer call sites.
"""

import ast
import os
from typing import List, Optional, Tuple

from taxonomy.lint_result_models import ILinterAdapter, LintResult, Severity, ISemanticTracer
from infrastructure.config_json_provider import load_json_config


# ─── Layer Rule Definitions ─────────────────────────────────────────────────
# DEFAULT rules (can be overridden via config file)
# Configurable via .auto_linter.json or auto_linter.config.yaml
# Example config:
#   governance_rules:
#     - from: surfaces
#       to: infrastructure
#       description: "Surface must not import Infrastructure"
#     - from: capabilities
#       to: surfaces
#       description: "Capabilities must not import Surface"

# Default empty — rules must be configured via config or SKILL.md guidance
# Community can define their own rules
LAYER_RULES: List[Tuple[str, str, str]] = []

# Default layer map
LAYER_MAP = {
    "infrastructure": "infrastructure",
    "capabilities": "capabilities",
    "surfaces": "surfaces",
    "domain": "domain",
    "agent": "agent",
    "taxonomy": "taxonomy",
}

def get_layer_rules() -> List[Tuple[str, str, str]]:
    """Helper to get governance rules from config."""
    try:
        config = load_json_config()
        if config and hasattr(config, 'governance_rules') and config.governance_rules:
            rules = []
            for r in config.governance_rules:
                if isinstance(r, dict):
                    rules.append((r.get('from', ''), r.get('to', ''), r.get('description', '')))
            return rules
    except Exception:
        pass
    return LAYER_RULES

def get_layer_map() -> dict:
    """Helper to get layer map from config."""
    try:
        config = load_json_config()
        if config and hasattr(config, 'layer_map') and config.layer_map:
            return config.layer_map
    except Exception:
        pass
    return LAYER_MAP

GOVERNANCE_CODE = "AES001"


# ─── AST Import Extractor ────────────────────────────────────────────────────

def _extract_imports(file_path: str) -> List[Tuple[int, str, Optional[str]]]:
    """
    Parse a Python file and return (line_number, module_path, imported_name) tuples
    for all import statements found.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    imports: List[Tuple[int, str, Optional[str]]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, str(alias.name), None))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    imports.append((node.lineno, str(node.module), str(alias.name)))
    return imports


def _detect_layer(module_path: str, layer_map: Optional[dict] = None) -> Optional[str]:
    """
    Given a dotted module path like 'src.infrastructure.adapters',
    return the AES layer name (key from layer_map).
    """
    if layer_map is None:
        layer_map = get_layer_map()
        
    parts = module_path.split(".")
    for part in parts:
        # Check if part matches any layer name or any component of a layer path
        for name, path in layer_map.items():
            path_parts = path.replace("\\", "/").split("/")
            if part == name or part in path_parts:
                return name
    return None


def _detect_file_layer(file_path: str, root_dir: str, layer_map: Optional[dict] = None) -> Optional[str]:
    """
    Derive the AES layer of a file from its path relative to the source root.
    """
    if layer_map is None:
        layer_map = get_layer_map()
        
    try:
        rel = os.path.relpath(file_path, root_dir).replace("\\", "/")
        # Check which layer path this file belongs to
        # Sort by path length descending to match most specific path first
        sorted_layers = sorted(layer_map.items(), key=lambda x: len(x[1]), reverse=True)
        for name, path in sorted_layers:
            if rel.startswith(path.strip("/")) or f"/{path.strip('/')}/" in f"/{rel}/":
                return name
    except Exception:
        pass
    return None


class GovernanceAdapter(ILinterAdapter):
    """
    Enforces AES architectural layer rules across Python files (Capability).

    Detects forbidden cross-layer imports and optionally identifies
    the call sites using ISemanticTracer.trace_call_chain for richer context.
    """

    def __init__(
        self,
        tracer: Optional[ISemanticTracer] = None,
        rules: Optional[List[Tuple[str, str, str]]] = None,
        layer_map: Optional[dict] = None
    ):
        self.tracer = tracer
        self._rules = rules
        self._layer_map = layer_map

    def name(self) -> str:
        return "governance"

    def _get_rules(self) -> List[Tuple[str, str, str]]:
        if self._rules is not None:
            return self._rules
        return get_layer_rules()

    def _get_layer_map(self) -> dict:
        if self._layer_map is not None:
            return self._layer_map
        return get_layer_map()

    def scan(self, path: str) -> List[LintResult]:
        """
        Scan path (file or directory) for architectural layer violations.
        Returns LintResult entries for each violation found.
        """
        root_dir = _resolve_root(path)
        python_files = _collect_python_files(path)
        results: List[LintResult] = []

        layer_rules = self._get_rules()
        layer_map = self._get_layer_map()

        for file_path in python_files:
            file_layer = _detect_file_layer(file_path, root_dir, layer_map)

            # agent is allowed to import everything — skip
            if file_layer == "agent" or file_layer is None:
                continue

            imports = _extract_imports(file_path)
            for line_no, module_path, imported_name in imports:
                target_layer = _detect_layer(module_path, layer_map)
                if target_layer is None:
                    continue

                for source_rule, forbidden_target, description in layer_rules:
                    if file_layer == source_rule and target_layer == forbidden_target:
                        violation = self._build_violation(
                            file_path=file_path,
                            line_no=line_no,
                            module_path=module_path,
                            description=description,
                            file_layer=file_layer,
                            target_layer=target_layer,
                            root_dir=root_dir,
                            imported_name=imported_name,
                        )
                        results.append(violation)
                        break  # Only report once per import line


        # Record history for trends analysis
        self._record_history(path, results)
        
        return results

    def apply_fix(self, path: str) -> bool:
        """Governance rules require architectural refactoring and cannot be auto-fixed."""
        return False

    def _record_history(self, path: str, results: List[LintResult]):
        """Save a snapshot of quality for trend analysis."""
        score = 100 - len(results) # Simplified score
        history_file = ".auto_lint_history"
        import json
        from datetime import datetime
        try:
            with open(history_file, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "path": path,
                    "score": max(0, score),
                    "violations": len(results)
                }) + "\n")
        except Exception:
            pass

    def _build_violation(
        self,
        file_path: str,
        line_no: int,
        module_path: str,
        description: str,
        file_layer: str,
        target_layer: str,
        root_dir: str,
        imported_name: Optional[str] = None,
    ) -> LintResult:
        """Construct a CRITICAL LintResult for a layer violation."""

        message = (
            f"[AES Layer Violation] {description}. "
            f"File in '{file_layer}' imports from '{target_layer}' via '{module_path}'."
        )

        # Optionally enrich with call chain context
        # Use imported name if available, otherwise fallback to leaf module name
        func_candidate = imported_name if imported_name and imported_name != "*" else module_path.split(".")[-1]
        related: List[str] = []
        tracer = self.tracer
        if root_dir and tracer:
            try:
                callers = tracer.trace_call_chain(root_dir, func_candidate)
                related = [f"CallSite: {c}" for c in callers[:3]]
            except Exception:
                pass

        return LintResult(
            file=file_path,
            line=line_no,
            column=0,
            code=GOVERNANCE_CODE,
            message=message,
            source="governance",
            severity=Severity.CRITICAL,
            related_locations=related,
        )


# ─── Private Helpers ─────────────────────────────────────────────────────────

def _resolve_root(path: str) -> str:
    """Find the project root (the dir containing 'src') from the given path."""
    current = os.path.abspath(path if os.path.isdir(path) else os.path.dirname(path))
    # Walk up to find 'src' parent
    while current and current != os.path.dirname(current):
        src_dir = os.path.join(str(current), "src")
        if os.path.isdir(src_dir):
            return str(current)
        current = os.path.dirname(current)
    return str(os.path.dirname(current) if not os.path.isdir(path) else path)


def _collect_python_files(path: str) -> List[str]:
    """Collect all .py files under a path (recursive for dirs, single for files)."""
    if os.path.isfile(path) and path.endswith(".py"):
        return [path]
    if not os.path.isdir(path):
        return []

    py_files: List[str] = []
    for dirpath, _, filenames in os.walk(path):
        # Skip cache dirs
        if "__pycache__" in dirpath or ".venv" in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(".py"):
                py_files.append(os.path.join(dirpath, filename))
    return py_files
