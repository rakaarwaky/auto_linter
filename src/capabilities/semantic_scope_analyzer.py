"""semantic_scope_analyzer — AST-based semantic scope analysis capability."""

from __future__ import annotations
import ast
import os
import re
import glob
from typing import Optional, List, Dict
from taxonomy import ISemanticTracer, FilePath, SymbolName, DirectoryPath, ScopeRef


class SemanticScopeAnalyzer(ISemanticTracer):
    """AST-based semantic scope analyzer for Python code."""

    def get_variant_dict(self, name: SymbolName | str) -> Dict[str, str]:
        n = str(name) if isinstance(name, SymbolName) else name
        words = re.findall(r'[A-Za-z][a-z0-9]*|[A-Z]+(?=[A-Z][a-z0-9]|\b)|[0-9]+', n)
        words = [w.lower() for w in words]
        if not words:
            return {"snake_case": n, "pascal_case": n, "camel_case": n, "screaming_snake": n.upper()}
        snake_case = "_".join(words)
        _rest = "".join(str(w).capitalize() for w in words[1:])
        return {
            "snake_case": snake_case,
            "camel_case": str(words[0]) + _rest,
            "pascal_case": "".join(str(w).capitalize() for w in words),
            "screaming_snake": snake_case.upper(),
        }

    def build_variants(self, name: SymbolName | str) -> List[str]:
        n = str(name) if isinstance(name, SymbolName) else name
        d = self.get_variant_dict(n)
        kebab = d["snake_case"].replace("_", "-")
        return list({n, d["snake_case"], d["camel_case"], d["pascal_case"], d["screaming_snake"], kebab})

    def show_enclosing_scope(self, file_path: FilePath | str, line: int) -> Optional[ScopeRef]:
        fp = str(file_path) if isinstance(file_path, FilePath) else file_path
        if not os.path.exists(fp):
            return None
        with open(fp, "r", encoding="utf-8") as f:
            source = f.read()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        class ScopeVisitor(ast.NodeVisitor):
            def __init__(self, target_line: int):
                self.target_line = target_line
                self.current_path: List[str] = []
                self.best_match: List[str] = []

            def generic_visit(self, node):
                is_scope = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                if is_scope:
                    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                        if node.lineno <= self.target_line <= node.end_lineno:
                            scope_name = f"class {node.name}" if isinstance(node, ast.ClassDef) else f"def {node.name}"
                            self.current_path.append(scope_name)
                            self.best_match = list(self.current_path)
                            super().generic_visit(node)
                            self.current_path.pop()
                            return
                super().generic_visit(node)

        visitor = ScopeVisitor(line)
        visitor.visit(tree)
        if visitor.best_match:
            return ScopeRef(name=" -> ".join(visitor.best_match), kind="")
        return None

    def find_flow(self, file_path: FilePath | str, var_name: SymbolName | str, start_line: Optional[int] = None) -> List[str]:
        fp = str(file_path) if isinstance(file_path, FilePath) else file_path
        vn = str(var_name) if isinstance(var_name, SymbolName) else var_name
        if not os.path.exists(fp):
            return []
        with open(fp, "r", encoding="utf-8") as f:
            lines = f.readlines()
            source = "".join(lines)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        flows = []
        target_scope: Optional[ast.AST] = tree

        if start_line is not None:
            class TargetScopeVisitor(ast.NodeVisitor):
                def __init__(self, target: int):
                    self.target = target
                    self.node: Optional[ast.AST] = None
                def generic_visit(self, node: ast.AST):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        lineno = getattr(node, "lineno", None)
                        end_lineno = getattr(node, "end_lineno", None)
                        if lineno is not None and end_lineno is not None:
                            if lineno <= self.target <= end_lineno:
                                self.node = node
                    super().generic_visit(node)
            tsv = TargetScopeVisitor(start_line)
            tsv.visit(tree)
            if tsv.node is not None:
                target_scope = tsv.node

        class FlowVisitor(ast.NodeVisitor):
            def visit_Name(self, node):
                if node.id == vn:
                    if hasattr(node, "lineno"):
                        line_text = lines[node.lineno - 1].strip()
                        if isinstance(node.ctx, ast.Store):
                            flows.append(f"Line {node.lineno} [Assignment]: {line_text}")
                        elif isinstance(node.ctx, ast.Load):
                            flows.append(f"Line {node.lineno} [Usage]: {line_text}")
                self.generic_visit(node)

            def visit_Call(self, node):
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == vn:
                        if hasattr(node, "lineno"):
                            line_text = lines[node.lineno - 1].strip()
                            flows.append(f"Line {node.lineno} [Mutation '{node.func.attr}']: {line_text}")
                self.generic_visit(node)

        if target_scope is not None:
            FlowVisitor().visit(target_scope)

        def extract_lineno(fstr: str) -> int:
            try:
                return int(fstr.split("Line ")[1].split(" ")[0])
            except Exception:  # pragma: no cover
                return 0  # pragma: no cover

        unique_flows = list(dict.fromkeys(flows))
        unique_flows.sort(key=extract_lineno)
        return unique_flows

    def trace_call_chain(self, root_dir: DirectoryPath | str, target_name: SymbolName | str) -> List[str]:
        root = str(root_dir) if isinstance(root_dir, DirectoryPath) else root_dir
        name = str(target_name) if isinstance(target_name, SymbolName) else target_name
        callers = []
        pattern = re.compile(rf"\b{name}\(")
        py_files = glob.glob(os.path.join(root, "**", "*.py"), recursive=True)
        for filepath in py_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except IOError:
                continue
            for i, line in enumerate(lines):
                if pattern.search(line) and f"def {name}" not in line:
                    rel_path = os.path.relpath(filepath, root)
                    callers.append(f"{rel_path}:{i+1} -> {line.strip()}")
        return callers

    def project_wide_rename(self, root_dir: DirectoryPath | str, old_name: SymbolName | str, new_name: SymbolName | str) -> int:
        root = str(root_dir) if isinstance(root_dir, DirectoryPath) else root_dir
        old = str(old_name) if isinstance(old_name, SymbolName) else old_name
        new = str(new_name) if isinstance(new_name, SymbolName) else new_name
        pattern = re.compile(rf'''
            (
                \"\"\"(?:\\.|[^\\])*?\"\"\" |
                \'\'\'(?:\\.|[^\\])*?\'\'\' |
                \"(?:\\.|[^\"\\])*\" |
                \'(?:\\.|[^\'\\])*\' |
                \#[^\n]*
            )
            |
            \b({re.escape(old)})\b
        ''', re.VERBOSE | re.DOTALL)

        def replacer(match):
            if match.group(1) is not None:
                return match.group(1)
            return new

        py_files = glob.glob(os.path.join(root, "**", "*.py"), recursive=True)
        modified_count: int = 0
        for filepath in py_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
            except IOError:
                continue
            if old not in source:
                continue
            new_source = pattern.sub(replacer, source)
            if new_source != source:
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_source)
                    modified_count += 1
                except IOError:
                    pass
        return modified_count
