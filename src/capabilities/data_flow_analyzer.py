"""data_flow_analyzer — Variable lifecycle tracking capability."""

from __future__ import annotations
import os
import re
from typing import List, Optional
from taxonomy import FilePath, SymbolName


def find_flow(file_path: FilePath | str, var_name: SymbolName | str, start_line: Optional[int] = None) -> List[str]:
    """Track assignments and usages of a variable in a JS/TS file."""
    fp = str(file_path) if isinstance(file_path, FilePath) else file_path
    vn = str(var_name) if isinstance(var_name, SymbolName) else var_name
    if not os.path.exists(fp):
        return []
    try:
        with open(fp, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return []

    from capabilities.scope_boundary_analyzer import find_scope_bounds
    scope_start, scope_end = find_scope_bounds(lines, start_line)
    flows: List[str] = []
    word_pattern = re.compile(rf"\b{re.escape(vn)}\b")
    assign_pattern = re.compile(
        rf"(?:const|let|var)\s+{re.escape(vn)}\s*=|(?<![=!<>]){re.escape(vn)}\s*="
    )
    mutation_pattern = re.compile(
        rf"\b{re.escape(vn)}\.(push|pop|shift|unshift|splice|sort|reverse|"
        rf"set|delete|add|assign|merge|update|append|extend)\b"
    )
    seen: set[str] = set()

    for i, raw_line in enumerate(lines):
        line_no = i + 1
        if scope_start is not None and line_no < scope_start:
            continue
        if scope_end is not None and line_no > scope_end:
            break
        if not word_pattern.search(raw_line):
            continue

        stripped = raw_line.strip()
        entry: Optional[str] = None
        match = mutation_pattern.search(raw_line)
        if match:
            entry = f"Line {line_no} [Mutation '{match.group(1)}']: {stripped}"
        elif assign_pattern.search(raw_line):
            entry = f"Line {line_no} [Assignment]: {stripped}"
        elif word_pattern.search(raw_line):
            entry = f"Line {line_no} [Usage]: {stripped}"

        if entry and entry not in seen:
            seen.add(entry)
            flows.append(entry)

    return flows
