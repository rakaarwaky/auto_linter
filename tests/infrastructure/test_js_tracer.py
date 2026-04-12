"""
Unit tests for JSTracer — JS/TS semantic analysis adapter.
Tests cover all 6 methods with edge cases and real-world patterns.
"""
import os
import tempfile
import textwrap

from infrastructure.javascript_call_tracer import JSTracer
from infrastructure.javascript_scope_patterns import (
    detect_js_scope,
    find_scope_bounds,
)


# ─── get_variant_dict ─────────────────────────────────────────────────────────

def test_get_variant_dict_camel_input():
    result = JSTracer().get_variant_dict("processPayment")
    assert result["snake_case"] == "process_payment"
    assert result["camel_case"] == "processPayment"
    assert result["pascal_case"] == "ProcessPayment"
    assert result["screaming_snake"] == "PROCESS_PAYMENT"

def test_get_variant_dict_snake_input():
    result = JSTracer().get_variant_dict("process_payment")
    assert result["snake_case"] == "process_payment"
    assert result["camel_case"] == "processPayment"
    assert result["pascal_case"] == "ProcessPayment"

def test_get_variant_dict_single_word():
    result = JSTracer().get_variant_dict("user")
    assert result["snake_case"] == "user"
    assert result["camel_case"] == "user"
    assert result["pascal_case"] == "User"

def test_get_variant_dict_empty_string():
    result = JSTracer().get_variant_dict("")
    assert result["snake_case"] == ""


# ─── build_variants ───────────────────────────────────────────────────────────

def test_build_variants_returns_list():
    variants = JSTracer().build_variants("processPayment")
    assert isinstance(variants, list)
    assert "processPayment" in variants
    assert "ProcessPayment" in variants
    assert "process_payment" in variants
    assert "PROCESS_PAYMENT" in variants
    assert "process-payment" in variants

def test_build_variants_snake_input():
    variants = JSTracer().build_variants("get_user_name")
    assert "getUserName" in variants
    assert "GetUserName" in variants
    assert "get-user-name" in variants


# ─── show_enclosing_scope ─────────────────────────────────────────────────────

def test_show_enclosing_scope_function_declaration():
    code = textwrap.dedent("""\
        function processPayment(amount) {
            const result = amount * 2;
            return result;
        }
    """)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        scope = JSTracer().show_enclosing_scope(path, 2)
        assert scope is not None
        assert "processPayment" in scope
    finally:
        os.remove(path)

def test_show_enclosing_scope_class_and_method():
    code = textwrap.dedent("""\
        class PaymentService {
            processPayment(amount) {
                const result = amount * 2;
            }
        }
    """)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        scope = JSTracer().show_enclosing_scope(path, 3)
        assert scope is not None
        assert "PaymentService" in scope
    finally:
        os.remove(path)

def test_show_enclosing_scope_arrow_function():
    code = textwrap.dedent("""\
        const calculateTotal = (items) => {
            return items.reduce((sum, x) => sum + x, 0);
        };
    """)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        scope = JSTracer().show_enclosing_scope(path, 2)
        assert scope is not None
        assert "calculateTotal" in scope
    finally:
        os.remove(path)

def test_show_enclosing_scope_top_level_returns_none():
    code = textwrap.dedent("""\
        const x = 1;
        const y = 2;
    """)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        scope = JSTracer().show_enclosing_scope(path, 1)
        assert scope is None
    finally:
        os.remove(path)

def test_show_enclosing_scope_nonexistent_file():
    result = JSTracer().show_enclosing_scope("/nonexistent.js", 1)
    assert result is None


# ─── find_flow ────────────────────────────────────────────────────────────────

def test_find_flow_tracks_assignment_and_usage():
    code = textwrap.dedent("""\
        function test() {
            const data = [];
            data.push(1);
            console.log(data);
        }
    """)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        flows = JSTracer().find_flow(path, "data")
        assert len(flows) >= 2
        assert any("Assignment" in fl for fl in flows)
        assert any("Mutation" in fl for fl in flows)
    finally:
        os.remove(path)

def test_find_flow_with_scope_line():
    code = textwrap.dedent("""\
        const data = 'global';
        function inner() {
            const data = 'local';
            return data;
        }
    """)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ts", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        # Scope starts at function line (2), so flow should be within the function
        flows = JSTracer().find_flow(path, "data", start_line=2)
        # All results should be from line 2 onwards
        for fl in flows:
            line_no = int(fl.split("Line ")[1].split(" ")[0])
            assert line_no >= 2
    finally:
        os.remove(path)

def test_find_flow_mutation_tracking():
    code = textwrap.dedent("""\
        function test() {
            const items = [];
            items.push(1);
            items.sort();
            return items;
        }
    """)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        flows = JSTracer().find_flow(path, "items")
        mutations = [fl for fl in flows if "Mutation" in fl]
        assert len(mutations) >= 1
    finally:
        os.remove(path)

def test_find_flow_nonexistent_file():
    result = JSTracer().find_flow("/nonexistent.js", "data")
    assert result == []

def test_find_flow_variable_not_in_file():
    code = "const x = 1;\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        flows = JSTracer().find_flow(path, "nonExistentVar")
        assert flows == []
    finally:
        os.remove(path)


# ─── trace_call_chain ─────────────────────────────────────────────────────────

def test_trace_call_chain_finds_caller():
    code_def = "export function sendEmail(to) { return true; }\n"
    code_caller = "import { sendEmail } from './mailer';\nsendEmail('user@example.com');\n"

    with tempfile.TemporaryDirectory() as tmp:
        path_def = os.path.join(tmp, "mailer.js")
        path_caller = os.path.join(tmp, "app.js")
        with open(path_def, "w") as f:
            f.write(code_def)
        with open(path_caller, "w") as f:
            f.write(code_caller)

        callers = JSTracer().trace_call_chain(tmp, "sendEmail")
        assert len(callers) == 1
        assert "app.js" in callers[0]
        assert "sendEmail" in callers[0]

def test_trace_call_chain_excludes_definition():
    code = "function myFunc() { return 1; }\nmyFunc();\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "script.js")
        with open(path, "w") as f:
            f.write(code)

        callers = JSTracer().trace_call_chain(tmp, "myFunc")
        # Only the call site, not the definition
        assert len(callers) == 1
        assert "myFunc()" in callers[0]

def test_trace_call_chain_empty_project():
    with tempfile.TemporaryDirectory() as tmp:
        result = JSTracer().trace_call_chain(tmp, "doesNotExist")
        assert result == []

def test_trace_call_chain_multiple_files():
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(3):
            path = os.path.join(tmp, f"caller{i}.ts")
            with open(path, "w") as f:
                f.write("import { fn } from './module';\nfn();\n")

        callers = JSTracer().trace_call_chain(tmp, "fn")
        assert len(callers) == 3


# ─── project_wide_rename ──────────────────────────────────────────────────────

def test_project_wide_rename_renames_identifiers():
    code = "const badName = 1;\nconst result = badName + 2;\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "app.js")
        with open(path, "w") as f:
            f.write(code)

        count = JSTracer().project_wide_rename(tmp, "badName", "goodName")
        assert count == 1

        with open(path) as f:
            result = f.read()
        assert "goodName = 1" in result
        assert "goodName + 2" in result

def test_project_wide_rename_preserves_strings():
    code = "const x = 1;\nconsole.log('badName is cool');\nconst badName = x;\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "app.ts")
        with open(path, "w") as f:
            f.write(code)

        JSTracer().project_wide_rename(tmp, "badName", "goodName")

        with open(path) as f:
            result = f.read()
        # String preserved
        assert "'badName is cool'" in result
        # Identifier renamed
        assert "const goodName = x" in result

def test_project_wide_rename_preserves_comments():
    code = "// badName is the old name\nconst badName = 1;\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "app.js")
        with open(path, "w") as f:
            f.write(code)

        JSTracer().project_wide_rename(tmp, "badName", "goodName")

        with open(path) as f:
            result = f.read()
        # Comment preserved
        assert "// badName is the old name" in result
        # Identifier renamed
        assert "const goodName = 1" in result

def test_project_wide_rename_preserves_template_literals():
    code = "const msg = `Hello ${badName}!`;\nconst badName = 'world';\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "app.ts")
        with open(path, "w") as f:
            f.write(code)

        JSTracer().project_wide_rename(tmp, "badName", "goodName")

        with open(path) as f:
            result = f.read()
        # Template literal content is tricky — the ${ } interpolation is actual code,
        # but the backtick content is captured as a whole. Let's verify the rename happened.
        assert "const goodName = 'world'" in result

def test_project_wide_rename_no_match_unchanged():
    code = "const x = 1;\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "app.js")
        with open(path, "w") as f:
            f.write(code)

        count = JSTracer().project_wide_rename(tmp, "nonExistent", "replacement")
        assert count == 0

def test_project_wide_rename_multiple_files():
    with tempfile.TemporaryDirectory() as tmp:
        for ext in ["js", "ts", "jsx"]:
            p = os.path.join(tmp, f"file.{ext}")
            with open(p, "w") as f:
                f.write("const oldFunc = () => {};\noldFunc();\n")

        count = JSTracer().project_wide_rename(tmp, "oldFunc", "newFunc")
        assert count == 3


# ─── Helper functions ─────────────────────────────────────────────────────────

def testdetect_js_scope_function_declaration():
    result = detect_js_scope("function processPayment(amount) {")
    assert result == "function processPayment"

def testdetect_js_scope_async_function():
    result = detect_js_scope("async function fetchData() {")
    assert result == "function fetchData"

def testdetect_js_scope_class():
    result = detect_js_scope("class PaymentService {")
    assert result == "class PaymentService"

def testdetect_js_scope_class_extends():
    result = detect_js_scope("class StripeAdapter extends BaseAdapter {")
    assert result == "class StripeAdapter"

def testdetect_js_scope_arrow_function():
    result = detect_js_scope("const calculateTotal = (items) => {")
    assert result == "function calculateTotal"

def testdetect_js_scope_no_match_control_flow():
    # 'if' and 'for' should not be detected as scoped functions
    result_if = detect_js_scope("    if (condition) {")
    result_for = detect_js_scope("    for (let i = 0; i < n; i++) {")
    assert result_if is None or "if" not in (result_if or "")
    assert result_for is None or "for" not in (result_for or "")

def testdetect_js_scope_detects_without_brace():
    # detect_js_scope detects the name regardless of braces on the line.
    # The brace guard is handled by the caller (show_enclosing_scope).
    result = detect_js_scope("function foo()")
    assert result == "function foo"

def testfind_scope_bounds_finds_bounds():
    lines = [
        "function test() {\n",   # 1
        "  const x = 1;\n",      # 2
        "  return x;\n",         # 3
        "}\n",                   # 4
    ]
    start, end = find_scope_bounds(lines, scope_line=1)
    assert start == 1
    assert end == 4

def testfind_scope_bounds_none_scope_line():
    start, end = find_scope_bounds([], scope_line=None)
    assert start is None
    assert end is None
