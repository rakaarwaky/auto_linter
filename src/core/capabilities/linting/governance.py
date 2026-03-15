"""
GovernanceAdapter — Architectural Layer Rule Enforcer (Capability).

AES Layer Rules (strict dependency direction):
  surfaces    --> core           (ALLOWED)
  surfaces    --> infrastructure (FORBIDDEN)
  core        --> infrastructure (FORBIDDEN)
  core        --> surfaces       (FORBIDDEN)
  infrastructure --> core._taxonomy (ALLOWED)
  infrastructure --> surfaces    (FORBIDDEN)
  bootstrap   --> *              (ALLOWED — wiring layer)

Detection strategy:
  1. Walk all Python files in the scanned path.
  2. For each file, use AST to extract all import targets.
  3. Apply layer rules to detect violations.
  4. Use PythonTracer.trace_call_chain to find cross-layer call sites
     when a caller in a forbidden layer directly invokes infra functions.
"""

import ast
import os
from typing import List, Optional, Tuple

from src.core._taxonomy.models import ILinterAdapter, LintResult, Severity, ISemanticTracer


# ─── Layer Rule Definitions ─────────────────────────────────────────────────

# Each rule: (source_layer_key, forbidden_target_key, description)
LAYER_RULES: List[Tuple[str, str, str]] = [
    ("surfaces", "infrastructure", "Surface layer must not import Infrastructure directly"),
    ("core",     "infrastructure", "Core layer must not import Infrastructure (use Taxonomy interfaces)"),
    ("core",     "surfaces",       "Core layer must not import Surface layer"),
    ("infrastructure", "surfaces", "Infrastructure layer must not import Surface layer"),
]

# Import path segment → layer name
LAYER_MAP = {
    "surfaces":     "surfaces",
    "core":         "core",
    "infrastructure": "infrastructure",
    "bootstrap":    "bootstrap",
}

GOVERNANCE_CODE = "AES001"


# ─── AST Import Extractor ────────────────────────────────────────────────────

def _extract_imports(file_path: str) -> List[Tuple[int, str]]:
    """
    Parse a Python file and return (line_number, module_path) tuples
    for all import statements found.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []

    imports: List[Tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, str(alias.name)))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.lineno, str(node.module)))
    return imports


def _detect_layer(module_path: str) -> Optional[str]:
    """
    Given a dotted module path like 'src.infrastructure.adapters.python',
    return the AES layer name or None if unknown.
    """
    parts = module_path.split(".")
    for part in parts:
        if part in LAYER_MAP:
            return LAYER_MAP[part]
    return None


def _detect_file_layer(file_path: str, root_dir: str) -> Optional[str]:
    """
    Derive the AES layer of a file from its path relative to the source root.
    """
    rel = os.path.relpath(file_path, root_dir)
    parts = rel.replace("\\", "/").split("/")
    for part in parts:
        if part in LAYER_MAP:
            return LAYER_MAP[part]
    return None


# ─── GovernanceAdapter ───────────────────────────────────────────────────────

class GovernanceAdapter(ILinterAdapter):
    """
    Enforces AES architectural layer rules across Python files (Capability).

    Detects forbidden cross-layer imports and optionally identifies
    the call sites using ISemanticTracer.trace_call_chain for richer context.
    """

    def __init__(self, tracer: Optional[ISemanticTracer] = None):
        self.tracer = tracer

    def name(self) -> str:
        return "governance"

    def scan(self, path: str) -> List[LintResult]:
        """
        Scan path (file or directory) for architectural layer violations.
        Returns LintResult entries for each violation found.
        """
        root_dir = _resolve_root(path)
        python_files = _collect_python_files(path)
        results: List[LintResult] = []

        for file_path in python_files:
            file_layer = _detect_file_layer(file_path, root_dir)

            # bootstrap is allowed to import everything — skip
            if file_layer == "bootstrap" or file_layer is None:
                continue

            imports = _extract_imports(file_path)
            for line_no, module_path in imports:
                target_layer = _detect_layer(module_path)
                if target_layer is None:
                    continue

                for source_rule, forbidden_target, description in LAYER_RULES:
                    if file_layer == source_rule and target_layer == forbidden_target:
                        violation = self._build_violation(
                            file_path=file_path,
                            line_no=line_no,
                            module_path=module_path,
                            description=description,
                            file_layer=file_layer,
                            target_layer=target_layer,
                            root_dir=root_dir,
                        )
                        results.append(violation)
                        break  # Only report once per import line


        return results

    def _build_violation(
        self,
        file_path: str,
        line_no: int,
        module_path: str,
        description: str,
        file_layer: str,
        target_layer: str,
        root_dir: str,
    ) -> LintResult:
        """Construct a CRITICAL LintResult for a layer violation."""

        message = (
            f"[AES Layer Violation] {description}. "
            f"File in '{file_layer}' imports from '{target_layer}' via '{module_path}'."
        )

        # Optionally enrich with call chain context
        # Extract the leaf module name as potential function target
        func_candidate = module_path.split(".")[-1]
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
