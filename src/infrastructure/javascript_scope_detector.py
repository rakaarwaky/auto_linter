"""JS Tracer - Enclosing scope detection for JS/TS files."""
from __future__ import annotations
import os
from typing import List, Optional, Tuple, cast

from infrastructure.javascript_scope_patterns import (
    detect_js_scope,
)


def show_enclosing_scope(file_path: str, line: int) -> Optional[str]:
    """Find the nearest enclosing function or class for a given 1-indexed line."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
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

    if best_match:
        return " -> ".join(best_match)
    return None
