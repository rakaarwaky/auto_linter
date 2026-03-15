"""
JSTracer — Semantic analysis adapter for JavaScript/TypeScript files.

Provides feature parity with PythonTracer using regex-based AST-equivalent
analysis (since there's no stdlib JS parser in Python). Implements:

  1. build_variants()      — naming convention variants
  2. show_enclosing_scope() — nearest enclosing function/class/arrow context
  3. find_flow()           — variable assignment and usage tracking
  4. trace_call_chain()    — cross-file caller detection
  5. get_variant_dict()    — structured naming variant dict
  6. project_wide_rename() — safe project-wide symbol rename (skips strings/comments)

Design principle:
  No external binaries (no Node.js, no acorn). Pure Python regex analysis
  for maximum portability and reliability within the linter daemon.
"""

from __future__ import annotations
import os
import re
from typing import List, Optional, Tuple, cast
from src.core._taxonomy.models import ISemanticTracer


# ─── Regex Patterns ──────────────────────────────────────────────────────────

# Function declarations and expressions
_FUNCTION_PATTERNS = [
    # function name(  or  async function name(
    re.compile(r"(?:async\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\("),
    # const name = (...) =>  or  const name = async (...) =>
    re.compile(r"(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][A-Za-z0-9_$]*)\s*=>"),
    # method shorthand inside class:  name(  or  async name(  (indented)
    re.compile(r"^\s+(?:async\s+|static\s+|private\s+|protected\s+|public\s+)*([A-Za-z_$][A-Za-z0-9_$]*)\s*\("),
]

# Class declarations: class Name  or  class Name extends Base
_CLASS_PATTERN = re.compile(r"class\s+([A-Za-z_$][A-Za-z0-9_$]*)(?:\s+extends\s+[A-Za-z_$][A-Za-z0-9_$]*)?")

# Variable assignment: const/let/var name =  or  name =
_ASSIGN_PATTERN = re.compile(r"(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=|^([A-Za-z_$][A-Za-z0-9_$]*)\s*=(?!=)")

# JS/TS file extensions
_JS_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")




class JSTracer(ISemanticTracer):
    """Regex-based semantic tracer for JavaScript/TypeScript files."""

    def get_variant_dict(self, name: str) -> dict:
        """
        Produces common naming variants mapped by their type.
        """
        # Split on underscores, camelCase boundaries, and hyphens
        words = re.findall(r"[A-Za-z][a-z0-9]*|[A-Z]+(?=[A-Z][a-z0-9]|\b)|[0-9]+", name)
        words = cast(List[str], [w.lower() for w in words])

        if not words:
            return {"snake_case": name, "camel_case": name, "pascal_case": name, "screaming_snake": name}

        snake_case = "_".join(words)
        _first = str(words[0])
        _rest_list = list(words[1:])
        _rest = "".join(str(w).capitalize() for w in _rest_list)
        camel_case = _first + _rest
        pascal_case = "".join(str(w).capitalize() for w in words)
        screaming_snake = snake_case.upper()

        return {
            "snake_case": snake_case,
            "camel_case": camel_case,
            "pascal_case": pascal_case,
            "screaming_snake": screaming_snake,
        }

    def build_variants(self, name: str) -> List[str]:
        """
        Produce common naming variants for a given symbol name.
        Example: processPayment -> process_payment, PROCESS_PAYMENT, ProcessPayment, process-payment
        """
        variants_dict = self.get_variant_dict(name)
        kebab_case = variants_dict["snake_case"].replace("_", "-")
        variants_set = {
            name,
            variants_dict["snake_case"],
            variants_dict["camel_case"],
            variants_dict["pascal_case"],
            variants_dict["screaming_snake"],
            kebab_case,
        }
        return list(variants_set)

    # ─── 2. Enclosing Scope ─────────────────────────────────────────────────

    def show_enclosing_scope(self, file_path: str, line: int) -> Optional[str]:
        """
        Finds the nearest enclosing function or class for a given 1-indexed line.
        Returns a breadcrumb string like 'class MyClass -> function processPayment'.
        Uses brace-counting to determine scope boundaries.
        """
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return None

        # We scan from the top, tracking open scopes with a stack
        # Stack entries: (scope_label, open_brace_count_at_entry)
        scope_stack: List[Tuple[str, int]] = []
        brace_depth = 0
        best_match: List[str] = []

        for i, raw_line in enumerate(lines):
            current_line_no = i + 1
            stripped = raw_line.strip()

            # Detect scope-opening declarations BEFORE counting braces on that line
            detected_scope = _detect_js_scope(stripped)
            braces_on_line = raw_line.count("{") - raw_line.count("}")

            # Pop scopes whose brace depth has closed
            while scope_stack:
                last_scope = cast(Tuple[str, int], scope_stack[-1])
                if brace_depth <= last_scope[1]:
                    scope_stack.pop()  # pragma: no cover
                else:
                    break

            if detected_scope and "{" in raw_line:
                cast(List[Tuple[str, int]], scope_stack).append((detected_scope, brace_depth))

            brace_depth += braces_on_line

            # Pop after brace_depth update if needed
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

    # ─── 3. Find Flow ────────────────────────────────────────────────────────

    def find_flow(self, file_path: str, var_name: str, start_line: Optional[int] = None) -> List[str]:
        """
        Tracks assignments and usages of a variable in a JS/TS file.
        Returns sorted list of flow strings: 'Line N [Assignment|Usage|Mutation]: code'.
        If scope_line is provided, restricts to the enclosing function scope.
        """
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return []

        # Determine scope bounds if scope_line is given
        scope_start, scope_end = _find_scope_bounds(lines, start_line)

        flows: List[str] = []
        # Escape name for exact word-boundary matching
        word_pattern = re.compile(rf"\b{re.escape(var_name)}\b")
        assign_pattern = re.compile(
            rf"(?:const|let|var)\s+{re.escape(var_name)}\s*=|(?<![=!<>]){re.escape(var_name)}\s*="
        )
        mutation_pattern = re.compile(
            rf"\b{re.escape(var_name)}\.(push|pop|shift|unshift|splice|sort|reverse|"
            rf"set|delete|add|assign|merge|update|append|extend)\b"
        )

        seen: set[str] = set()

        for i, raw_line in enumerate(lines):
            line_no = i + 1

            # Scope filtering
            _ss = scope_start
            _se = scope_end
            if _ss is not None:
                if line_no < _ss:
                    continue
            if _se is not None:
                if line_no > _se:
                    break

            # Skip lines that don't mention the variable at all
            if not word_pattern.search(raw_line):
                continue

            stripped = raw_line.strip()
            entry: Optional[str] = None

            match = mutation_pattern.search(raw_line)
            if match:
                method = str(match.group(1))
                entry = f"Line {line_no} [Mutation '{method}']: {stripped}"
            elif assign_pattern.search(raw_line):
                entry = f"Line {line_no} [Assignment]: {stripped}"
            elif word_pattern.search(raw_line):
                entry = f"Line {line_no} [Usage]: {stripped}"

            if entry and entry not in seen:
                seen.add(entry)
                flows.append(entry)

        return flows

    # ─── 4. Trace Call Chain ─────────────────────────────────────────────────

    def trace_call_chain(self, root_dir: str, target_name: str) -> List[str]:
        """
        Searches for callers of function_name across JS/TS files in root_dir.
        Returns list of 'relative/path:line -> code_snippet' strings.
        Excludes the definition line itself (lines containing 'function name(').
        """
        import glob

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

    # ─── 5. Project-Wide Rename ──────────────────────────────────────────────

    def project_wide_rename(self, root_dir: str, old_name: str, new_name: str) -> int:
        """
        Renames a symbol project-wide across JS/TS files.
        Uses a smart regex that skips string literals, template literals, and comments.
        Returns the number of files modified.
        """
        import glob

        # Match strings, template literals, and comments — keep them unchanged.
        # Group 1: content to skip. Group 2 (no group name): symbol to rename.
        pattern = re.compile(
            rf"""
            (
                `(?:\\.|[^`\\])*`             |   # template literals
                \"(?:\\.|[^\"\\])*\"          |   # double-quoted strings
                '(?:\\.|[^'\\])*'             |   # single-quoted strings
                //[^\n]*                      |   # single-line comments
                /\*(?:.|\n)*?\*/                  # multi-line comments
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
                    modified_count = int(modified_count) + 1
                except OSError:
                    pass

        return modified_count


# ─── Private Helpers ──────────────────────────────────────────────────────────

def _detect_js_scope(stripped_line: str) -> Optional[str]:
    """
    Given a stripped line of JS/TS, detect if it opens a named scope.
    Returns a label string or None.
    """
    # Class
    match = _CLASS_PATTERN.search(stripped_line)
    if match:
        return f"class {match.group(1)}"

    # Named function declaration or expression
    for pattern in _FUNCTION_PATTERNS:
        match = pattern.search(stripped_line)
        if match:
            name = match.group(1)
            # Avoid false positives on control-flow keywords
            if name not in {"if", "for", "while", "switch", "catch", "else"}:
                return f"function {name}"

    return None


def _find_scope_bounds(
    lines: list[str], scope_line: Optional[int]
) -> tuple[Optional[int], Optional[int]]:
    """
    Given a 1-indexed scope_line, find the start/end line numbers (inclusive)
    of the enclosing function body using brace counting.
    Returns (start_line, end_line) or (None, None).
    """
    if scope_line is None:
        return None, None

    # Scan up from scope_line to find the function opener
    brace_depth: int = 0
    scope_start: Optional[int] = None
    scope_end: Optional[int] = None

    # Forward scan from scope_line to find where the enclosing block starts
    for i in range(scope_line - 1, len(lines)):
        line = lines[i]
        if "{" in line and scope_start is None:
            scope_start = i + 1
            brace_depth = 1
            continue
        if scope_start is not None:
            d_change = line.count("{") - line.count("}")
            _bd = brace_depth
            brace_depth = _bd + d_change
            if brace_depth <= 0:
                scope_end = i + 1
                break

    return scope_start, scope_end
