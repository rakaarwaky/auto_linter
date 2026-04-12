"""call_chain_analyzer — Call chain analysis capability."""

from __future__ import annotations
import os
import re
import glob
from typing import List, Optional

from capabilities.naming_variant_generator import get_variant_dict as _get_variant_dict, build_variants as _build_variants
from capabilities.scope_boundary_analyzer import show_enclosing_scope as _show_enclosing_scope
from capabilities.data_flow_analyzer import find_flow as _find_flow
from taxonomy import ISemanticTracer, FilePath, SymbolName, DirectoryPath, ScopeRef


class CallChainAnalyzer(ISemanticTracer):
    """Call chain analyzer for JavaScript/TypeScript files."""

    def get_variant_dict(self, name: SymbolName | str) -> dict:
        return _get_variant_dict(str(name) if isinstance(name, SymbolName) else name)

    def build_variants(self, name: SymbolName | str) -> List[str]:
        return _build_variants(str(name) if isinstance(name, SymbolName) else name)

    def show_enclosing_scope(self, file_path: FilePath | str, line: int) -> Optional[ScopeRef]:
        result = _show_enclosing_scope(
            str(file_path) if isinstance(file_path, FilePath) else file_path, line
        )
        if result:
            return ScopeRef(name=result)
        return None

    def find_flow(self, file_path: FilePath | str, var_name: SymbolName | str, start_line: Optional[int] = None) -> List[str]:
        return _find_flow(
            str(file_path) if isinstance(file_path, FilePath) else file_path,
            str(var_name) if isinstance(var_name, SymbolName) else var_name,
            start_line,
        )

    def trace_call_chain(self, root_dir: DirectoryPath | str, target_name: SymbolName | str) -> List[str]:
        callers: List[str] = []
        name = str(target_name) if isinstance(target_name, SymbolName) else target_name
        root = str(root_dir) if isinstance(root_dir, DirectoryPath) else root_dir
        call_pattern = re.compile(rf"\b{re.escape(name)}\s*\(")
        def_pattern = re.compile(rf"(?:function|class)\s+{re.escape(name)}\b")
        js_files: List[str] = []
        for ext in ("*.js", "*.jsx", "*.ts", "*.tsx", "*.mjs"):
            js_files.extend(glob.glob(os.path.join(root, "**", ext), recursive=True))
        for filepath in js_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    file_lines = f.readlines()
            except OSError:
                continue
            for i, line in enumerate(file_lines):
                if call_pattern.search(line) and not def_pattern.search(line):
                    rel_path = os.path.relpath(filepath, root)
                    callers.append(f"{rel_path}:{i+1} -> {line.strip()}")
        return callers

    def project_wide_rename(self, root_dir: DirectoryPath | str, old_name: SymbolName | str, new_name: SymbolName | str) -> int:
        root = str(root_dir) if isinstance(root_dir, DirectoryPath) else root_dir
        old = str(old_name) if isinstance(old_name, SymbolName) else old_name
        new = str(new_name) if isinstance(new_name, SymbolName) else new_name
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
            \b({re.escape(old)})\b
            """,
            re.VERBOSE | re.DOTALL,
        )

        def replacer(match: re.Match) -> str:
            if match.group(1) is not None:
                return match.group(1)
            return new

        js_files: List[str] = []
        for ext in ("*.js", "*.jsx", "*.ts", "*.tsx", "*.mjs"):
            js_files.extend(glob.glob(os.path.join(root, "**", ext), recursive=True))

        modified_count: int = 0
        for filepath in js_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
            except OSError:
                continue
            if old not in source:
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
