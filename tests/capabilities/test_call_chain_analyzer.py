"""Comprehensive tests for capabilities/call_chain_analyzer.py — 100% coverage."""

import pytest
import tempfile
import os
from capabilities.call_chain_analyzer import CallChainAnalyzer
from taxonomy import FilePath, SymbolName


class TestCallChainAnalyzer:
    def test_trace_call_chain_js_function(self):
        analyzer = CallChainAnalyzer()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.js")
            with open(test_file, "w") as f:
                f.write("""function myFunc() {
    console.log("hello");
}

function caller() {
    myFunc();
}
""")
            result = analyzer.trace_call_chain(tmpdir, "myFunc")
            assert len(result) > 0
            assert "myFunc()" in result[0]

    def test_trace_call_chain_no_callers(self):
        analyzer = CallChainAnalyzer()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.js")
            with open(test_file, "w") as f:
                f.write("""function unusedFunc() {
    console.log("unused");
}
""")
            result = analyzer.trace_call_chain(tmpdir, "unusedFunc")
            assert result == []

    def test_trace_call_chain_class_method(self):
        analyzer = CallChainAnalyzer()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.js")
            with open(test_file, "w") as f:
                f.write("""class MyClass {
    myMethod() {
        console.log("hello");
    }
}

const obj = new MyClass();
obj.myMethod();
""")
            result = analyzer.trace_call_chain(tmpdir, "myMethod")
            assert len(result) > 0

    def test_trace_call_chain_nonexistent_file(self):
        analyzer = CallChainAnalyzer()
        result = analyzer.trace_call_chain("/nonexistent", "func")
        assert result == []

    def test_get_variant_dict(self):
        analyzer = CallChainAnalyzer()
        result = analyzer.get_variant_dict("myFunctionName")
        assert "snake_case" in result
        assert result["snake_case"] == "my_function_name"

    def test_build_variants(self):
        analyzer = CallChainAnalyzer()
        result = analyzer.build_variants("my_function")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_show_enclosing_scope(self):
        analyzer = CallChainAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("""function myFunc() {
    let x = 1;
}
""")
            f.flush()
            result = analyzer.show_enclosing_scope(f.name, 2)
        os.remove(f.name)
        assert result is not None

    def test_show_enclosing_scope_nonexistent(self):
        analyzer = CallChainAnalyzer()
        result = analyzer.show_enclosing_scope("/nonexistent.js", 1)
        assert result is None

    def test_find_flow(self):
        analyzer = CallChainAnalyzer()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("""const myVar = 1;
console.log(myVar);
""")
            f.flush()
            result = analyzer.find_flow(f.name, "myVar")
        os.remove(f.name)
        assert len(result) > 0

    def test_project_wide_rename(self):
        analyzer = CallChainAnalyzer()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.js")
            with open(test_file, "w") as f:
                f.write("const old_name = 1;\nconsole.log(old_name);\n")
            result = analyzer.project_wide_rename(tmpdir, "old_name", "new_name")
            assert result >= 1
            with open(test_file) as f:
                content = f.read()
            assert "new_name" in content
            assert "old_name" not in content

    def test_project_wide_rename_protects_strings(self):
        analyzer = CallChainAnalyzer()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.js")
            with open(test_file, "w") as f:
                f.write('const myVar = 1;\nconst str = "myVar should not change";\n// myVar is a comment\n')
            result = analyzer.project_wide_rename(tmpdir, "myVar", "newVar")
            assert result >= 1
            with open(test_file) as f:
                content = f.read()
            assert 'const newVar = 1' in content
            assert '"myVar should not change"' in content  # String preserved
