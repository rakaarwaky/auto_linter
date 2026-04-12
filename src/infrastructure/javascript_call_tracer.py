"""JSTracer — Semantic analysis adapter for JavaScript/TypeScript files.

Delegates to granular modules:
- js_patterns.py        — regex patterns, scope detection
- js_tracer_naming.py   — naming variants
- js_tracer_scope.py    — enclosing scope detection
- js_tracer_flow.py     — variable flow tracking
- js_tracer_chain.py    — call chain tracing
- js_tracer_rename.py   — project-wide rename
"""
from __future__ import annotations
import os
import re
import glob
from typing import List, Optional

from infrastructure.javascript_naming_variants import (
    get_variant_dict as _get_variant_dict,
    build_variants as _build_variants,
)
from infrastructure.javascript_scope_detector import (
    show_enclosing_scope as _show_enclosing_scope,
)
from infrastructure.javascript_flow_tracker import (
    find_flow as _find_flow,
)
from taxonomy.lint_result_models import ISemanticTracer


class JSTracer(ISemanticTracer):
    """Regex-based semantic tracer for JavaScript/TypeScript files."""

    def get_variant_dict(self, name: str) -> dict:
        return _get_variant_dict(name)

    def build_variants(self, name: str) -> List[str]:
        return _build_variants(name)

    def show_enclosing_scope(self, file_path: str, line: int) -> Optional[str]:
        return _show_enclosing_scope(file_path, line)

    def find_flow(self, file_path: str, var_name: str, start_line: Optional[int] = None) -> List[str]:
        return _find_flow(file_path, var_name, start_line)

    def trace_call_chain(self, root_dir: str, target_name: str) -> List[str]:
        callers: List[str] = []
        call_pattern = re.compile(rf"\b{re.escape(target_name)}\s*\(")
        def_pattern = re.compile(rf"(?:function|class)\s+{re.escape(target_name)}\b")
        js_files: List[str] = []
        for ext in ("*.js", "*.jsx", "*.ts", "*.tsx", "*.mjs"):
            js_files.extend(glob.glob(os.path.join(root_dir, "**", ext), recursive=True))
        for filepath in js_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    file_lines = f.readlines()
            except OSError:
                continue
            for i, line in enumerate(file_lines):
                if call_pattern.search(line) and not def_pattern.search(line):
                    rel_path = os.path.relpath(filepath, root_dir)
                    callers.append(f"{rel_path}:{i+1} -> {line.strip()}")
        return callers

    def project_wide_rename(self, root_dir: str, old_name: str, new_name: str) -> int:
        pattern = re.compile(
            rf"""
            (
                `(?:\\.|[^`\\])*`             |
                \"(?:\\.|[^\"\\])*\"          |
                '(?:\\.|[^'\\])*'             |
                //[^\n]*                      |
                /\*(?:.|\n)*?\*/
            )
            |
            \b({re.escape(old_name)})\b
            """,
            re.VERBOSE | re.DOTALL,
        )

        def replacer(match: re.Match) -> str:
            if match.group(1) is not None:
                return match.group(1)
            return new_name

        js_files: List[str] = []
        for ext in ("*.js", "*.jsx", "*.ts", "*.tsx", "*.mjs"):
            js_files.extend(glob.glob(os.path.join(root_dir, "**", ext), recursive=True))

        modified_count: int = 0
        for filepath in js_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
            except OSError:
                continue
            if old_name not in source:
                continue
            new_source = pattern.sub(replacer, source)
            if new_source != source:
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_source)
                    modified_count += 1
                except OSError:
                    pass
        return modified_count
