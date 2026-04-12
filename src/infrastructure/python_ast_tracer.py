import ast
import os
import re
from typing import Optional, List, Dict
from taxonomy.lint_result_models import ISemanticTracer

class PythonTracer(ISemanticTracer):
    """AST-based tracer for Python code to enrich lint context."""

    def get_variant_dict(self, name: str) -> Dict[str, str]:
        """
        Produces common naming variants mapped by their type.
        """
        words = re.findall(r'[A-Za-z][a-z0-9]*|[A-Z]+(?=[A-Z][a-z0-9]|\b)|[0-9]+', name)
        words = [w.lower() for w in words]
        
        if not words:
            return {"snake_case": name, "pascal_case": name, "camel_case": name, "screaming_snake": name.upper()}
            
        snake_case = "_".join(words)
        _first = str(words[0])
        # Use explicit loop for slicing consistency
        _rest = []
        for i in range(1, len(words)):
            _rest.append(str(words[i]).capitalize())
        camel_case = _first + "".join(_rest)
        pascal_case = "".join(str(w).capitalize() for w in words)
        screaming_snake = snake_case.upper()
        
        res: Dict[str, str] = {
            "snake_case": snake_case,
            "camel_case": camel_case,
            "pascal_case": pascal_case,
            "screaming_snake": screaming_snake,
        }
        return res

    def build_variants(self, name: str) -> List[str]:
        """
        Produce common naming variants for a given base variable/function name.
        Example: process_payment -> processPayment, ProcessPayment, PROCESS_PAYMENT, process-payment
        """
        variants_dict = self.get_variant_dict(name=name)
        sc = variants_dict.get("snake_case", name)
        ss = variants_dict.get("screaming_snake", name.upper())
        cc = variants_dict.get("camel_case", name)
        pc = variants_dict.get("pascal_case", name)
        
        kebab_case = sc.replace("_", "-")
        variants_set = {name, sc, ss, cc, pc, kebab_case}
        return list(variants_set)

    def show_enclosing_scope(self, file_path: str, line: int) -> Optional[str]:
        """
        Finds the nearest enclosing function or class for a given line.
        Returns a string like 'class MyClass -> def my_func'.
        """
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, "r", encoding="utf-8") as f:
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
            return " -> ".join(visitor.best_match)
        return None
        
    def find_flow(self, file_path: str, var_name: str, start_line: Optional[int] = None) -> List[str]:
        """
        Tracks assignments and mutations of a variable in the local scope.
        Returns a list of code snippets and line numbers tracking the flow.
        """
        if not os.path.exists(file_path):
            return []
            
        with open(file_path, "r", encoding="utf-8") as f:
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
                        # Safely check for line numbers which might be None in some AST versions
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
                if node.id == var_name:
                    if hasattr(node, "lineno"):
                        line_text = lines[node.lineno - 1].strip()
                        if isinstance(node.ctx, ast.Store):
                            flows.append(f"Line {node.lineno} [Assignment]: {line_text}")
                        elif isinstance(node.ctx, ast.Load):
                            flows.append(f"Line {node.lineno} [Usage]: {line_text}")
                self.generic_visit(node)
                
            def visit_Call(self, node):
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == var_name:
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
                return 0       # pragma: no cover
                
        unique_flows = list(dict.fromkeys(flows))
        unique_flows.sort(key=extract_lineno)
        return unique_flows

    def trace_call_chain(self, root_dir: str, target_name: str) -> List[str]:
        """
        Searches for callers across Python files using regex scanning and formatting.
        """
        import glob
        callers = []
        
        pattern = re.compile(rf"\b{target_name}\(")
        
        py_files = glob.glob(os.path.join(root_dir, "**", "*.py"), recursive=True)
        for filepath in py_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except IOError:
                continue
                
            for i, line in enumerate(lines):
                if pattern.search(line):
                    if f"def {target_name}" not in line:
                        rel_path = os.path.relpath(filepath, root_dir)
                        code_snippet = line.strip()
                        callers.append(f"{rel_path}:{i+1} -> {code_snippet}")
            
        return callers

    def project_wide_rename(self, root_dir: str, old_name: str, new_name: str) -> int:
        """
        Renames a symbol project-wide using smart regex that ignores strings and comments.
        Returns the number of files modified.
        """
        import glob
        
        pattern = re.compile(rf'''
            (
                \"\"\"(?:\\.|[^\\])*?\"\"\" | 
                \'\'\'(?:\\.|[^\\])*?\'\'\' |
                \"(?:\\.|[^\"\\])*\" |
                \'(?:\\.|[^\'\\])*\' |
                \#[^\n]*
            )
            |
            \b({re.escape(old_name)})\b
        ''', re.VERBOSE | re.DOTALL)
        
        def replacer(match):
            if match.group(1) is not None:
                return match.group(1)
            else:
                return new_name
                
        py_files = glob.glob(os.path.join(root_dir, "**", "*.py"), recursive=True)
        modified_count: int = 0
        for filepath in py_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()
            except IOError:
                continue
                
            if old_name not in source:
                continue
                
            new_source = pattern.sub(replacer, source)
            
            if new_source != source:
                try:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_source)
                    # Explicit cast to int for Pyre tracking
                    modified_count = int(modified_count) + 1
                except IOError:
                    pass
            
        return modified_count
