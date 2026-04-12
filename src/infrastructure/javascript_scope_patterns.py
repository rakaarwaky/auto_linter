"""JS/TS regex patterns and scope detection helpers."""
from __future__ import annotations
import re
from typing import List, Optional, Tuple, cast

# Function declarations and expressions
_FUNCTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\("),
    re.compile(r"(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][A-Za-z0-9_$]*)\s*=>"),
    re.compile(r"^\s+(?:async\s+|static\s+|private\s+|protected\s+|public\s+)*([A-Za-z_$][A-Za-z0-9_$]*)\s*\("),
]

_CLASS_PATTERN = re.compile(r"class\s+([A-Za-z_$][A-Za-z0-9_$]*)(?:\s+extends\s+[A-Za-z_$][A-Za-z0-9_$]*)?")

_JS_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")


def detect_js_scope(stripped_line: str) -> Optional[str]:
    """Detect if a stripped JS/TS line opens a named scope."""
    match = _CLASS_PATTERN.search(stripped_line)
    if match:
        return f"class {match.group(1)}"
    for pattern in _FUNCTION_PATTERNS:
        match = pattern.search(stripped_line)
        if match:
            name = match.group(1)
            if name not in {"if", "for", "while", "switch", "catch", "else"}:
                return f"function {name}"
    return None


def find_scope_bounds(
    lines: list[str], scope_line: Optional[int]
) -> tuple[Optional[int], Optional[int]]:
    """Find start/end line numbers of enclosing function body via brace counting."""
    if scope_line is None:
        return None, None
    brace_depth = 0
    scope_start: Optional[int] = None
    scope_end: Optional[int] = None
    for i in range(scope_line - 1, len(lines)):
        line = lines[i]
        if "{" in line and scope_start is None:
            scope_start = i + 1
            brace_depth = 1
            continue
        if scope_start is not None:
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0:
                scope_end = i + 1
                break
    return scope_start, scope_end
