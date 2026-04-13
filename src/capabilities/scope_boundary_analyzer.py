"""scope_boundary_analyzer — JS/TS scope boundary detection."""

from __future__ import annotations
import os
import re
from typing import List, Optional, Tuple, cast
from taxonomy import FilePath


_FUNCTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\("),
    re.compile(r"(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][A-Za-z0-9_$]*)\s*=>"),
    re.compile(r"^(?:async\s+|static\s+|private\s+|protected\s+|public\s+)*([A-Za-z_$][A-Za-z0-9_$]*)\s*\("),
]

_CLASS_PATTERN = re.compile(r"class\s+([A-Za-z_$][A-Za-z0-9_$]*)(?:\s+extends\s+[A-Za-z_$][A-Za-z0-9_$]*)?")


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


def find_scope_bounds(lines: list[str], scope_line: Optional[int]) -> tuple[Optional[int], Optional[int]]:
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


def show_enclosing_scope(file_path: FilePath | str, line: int) -> Optional[str]:
    """Find the nearest enclosing function or class for a given 1-indexed line."""
    fp = str(file_path) if isinstance(file_path, FilePath) else file_path
    if not os.path.exists(fp):
        return None
    try:
        with open(fp, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return None

    scope_stack: List[Tuple[str, int]] = []
    brace_depth = 0
    best_match: List[str] = []

    for i, raw_line in enumerate(lines):
        current_line_no = i + 1
        stripped = raw_line.strip()
        detected_scope = detect_js_scope(stripped)
        braces_on_line = raw_line.count("{") - raw_line.count("}")

        while scope_stack:
            last_scope = cast(Tuple[str, int], scope_stack[-1])
            if brace_depth <= last_scope[1]:
                scope_stack.pop()  # pragma: no cover
            else:
                break

        if detected_scope and "{" in raw_line:
            cast(List[Tuple[str, int]], scope_stack).append((detected_scope, brace_depth))

        brace_depth += braces_on_line

        while scope_stack:
            last_scope = cast(Tuple[str, int], scope_stack[-1])
            if brace_depth <= last_scope[1]:
                scope_stack.pop()
            else:
                break

        if current_line_no == line:
            best_match = [s[0] for s in scope_stack]
            break

    return " -> ".join(best_match) if best_match else None
