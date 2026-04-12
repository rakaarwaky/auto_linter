"""linting_governance_adapter — Architectural layer rule enforcer."""
from typing import List, Tuple, Optional
import ast
import os

try:
    from taxonomy.lint_result_models import ILinterAdapter, LintResult, Severity
except ImportError:
    from lint_result_models import ILinterAdapter, LintResult, Severity


# ─── Layer Rule Definitions ─────────────────────────────────────────────────
# DEFAULT rules - can be overridden via config file
# Configurable via .auto_linter.json or auto_linter.config.yaml

# Default empty - hanya dari config
LAYER_RULES: List[Tuple[str, str, str]] = []

LAYER_MAP: dict = {}

GOVERNANCE_CODE = "AES001"


def get_layer_rules() -> List[Tuple[str, str, str]]:
    """Get governance rules - from config if available, else default."""
    try:
        from infrastructure.config_json_provider import load_json_config
        from infrastructure.config_validation_provider import load_yaml_config

        config = load_json_config() or load_yaml_config()
        if config and hasattr(config, 'governance_rules') and config.governance_rules:
            rules = []
            for rule in config.governance_rules:
                if isinstance(rule, dict):
                    rules.append((
                        rule.get('from', ''),
                        rule.get('to', ''),
                        rule.get('description', '')
                    ))
            if rules:
                return rules
    except Exception:
        pass

    return LAYER_RULES

def get_layer_map() -> dict:
    """Get layer map - from config, else defaults."""
    default_map = {
        "infrastructure": "infrastructure",
        "capabilities": "capabilities",
        "surfaces": "surfaces",
        "domain": "domain",
        "agent": "agent",
        "taxonomy": "taxonomy",
    }
    try:
        from infrastructure.config_json_provider import load_json_config
        from infrastructure.config_validation_provider import load_yaml_config

        config = load_json_config() or load_yaml_config()
        if config and hasattr(config, 'layer_map') and config.layer_map:
            merged = default_map.copy()
            merged.update(config.layer_map)
            return merged
    except Exception:
        pass

    return default_map


# ─── AST Import Extractor ───────────────────────────────────────────────────

def _extract_imports(file_path: str) -> List[Tuple[int, str]]:
    """Extract (line_number, module_path) tuples from a Python file."""
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
    """Return the AES layer name from a dotted module path."""
    parts = module_path.split(".")
    layer_map = get_layer_map()
    for part in parts:
        if part in layer_map:
            return layer_map[part]
    return None


def _detect_file_layer(file_path: str, root_dir: str) -> Optional[str]:
    """Derive the AES layer of a file from its path relative to the source root."""
    rel = os.path.relpath(file_path, root_dir)
    parts = rel.replace("\\", "/").split("/")
    layer_map = get_layer_map()
    for part in parts:
        if part in layer_map:
            return layer_map[part]
    return None


class GovernanceAdapter(ILinterAdapter):
    """Enforces AES architectural layer rules across Python files."""

    def __init__(self, tracer=None):
        """Accept optional tracer for compatibility with capabilities version."""
        self.tracer = tracer

    def name(self) -> str:
        return "governance"

    def lint(self, path: str) -> List[LintResult]:
        """Lint a single file for cross-layer imports."""
        results: List[LintResult] = []
        if not path.endswith(".py"):
            return results

        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(path)))

        # Extract imports from this file
        for line_no, module in _extract_imports(path):
            target_layer = _detect_layer(module)
            if target_layer is None:
                continue

            source_layer = _detect_file_layer(path, root_dir)
            if source_layer is None:
                continue

            # Check against configured rules
            for source_rule, forbidden_target, description in get_layer_rules():
                if source_layer == source_rule and target_layer == forbidden_target:
                    results.append(LintResult(
                        file=path,
                        line=line_no,
                        column=0,
                        code=GOVERNANCE_CODE,
                        message=description,
                        source="governance",
                        severity=Severity.CRITICAL,
                    ))

        return results

    def apply_fix(self, path: str) -> bool:
        """Governance rules require architectural refactoring and cannot be auto-fixed."""
        return False

    def scan(self, path: str) -> List[LintResult]:
        """Scan a file or directory for governance violations."""
        if os.path.isfile(path):
            return self.lint(path)

        results: List[LintResult] = []
        for dirpath, _, filenames in os.walk(path):
            if "__pycache__" in dirpath or ".venv" in dirpath:
                continue
            for filename in filenames:
                if filename.endswith(".py"):
                    filepath = os.path.join(dirpath, filename)
                    results.extend(self.lint(filepath))
        return results
