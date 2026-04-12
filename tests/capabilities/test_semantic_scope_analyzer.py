"""Tests for capabilities/semantic_scope_analyzer.py."""

import os
import pytest
from pathlib import Path
from capabilities.semantic_scope_analyzer import SemanticScopeAnalyzer
from taxonomy.lint_identifier_vo import SymbolName, FilePath, DirectoryPath


class TestSemanticScopeAnalyzer:
    def test_analyzer_initialization(self):
        analyzer = SemanticScopeAnalyzer()
        assert analyzer is not None

    def test_get_variant_dict_snake(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.get_variant_dict("hello_world")
        assert result["snake_case"] == "hello_world"
        assert result["camel_case"] == "helloWorld"
        assert result["pascal_case"] == "HelloWorld"
        assert result["screaming_snake"] == "HELLO_WORLD"

    def test_get_variant_dict_camel(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.get_variant_dict("helloWorld")
        assert "hello" in result["snake_case"]
        assert "world" in result["snake_case"]

    def test_get_variant_dict_pascal(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.get_variant_dict("HelloWorld")
        assert result["pascal_case"] == "HelloWorld"

    def test_get_variant_dict_single_word(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.get_variant_dict("test")
        assert result["snake_case"] == "test"
        assert result["pascal_case"] == "Test"

    def test_get_variant_dict_empty(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.get_variant_dict("")
        assert result["snake_case"] == ""
        assert result["screaming_snake"] == ""

    def test_get_variant_dict_with_numbers(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.get_variant_dict("test123")
        assert "123" in result["snake_case"]

    def test_get_variant_dict_symbol_name(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.get_variant_dict(SymbolName(value="hello_world"))
        assert result["snake_case"] == "hello_world"

    def test_build_variants(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.build_variants("hello_world")
        assert "hello_world" in result
        assert "helloWorld" in result
        assert "HelloWorld" in result
        assert "HELLO_WORLD" in result
        assert "hello-world" in result

    def test_build_variants_empty(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.build_variants("")
        assert "" in result

    def test_build_variants_symbol_name(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.build_variants(SymbolName(value="hello_world"))
        assert "hello_world" in result


class TestShowEnclosingScope:
    def test_nonexistent_file(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.show_enclosing_scope("/nonexistent/file.py", 10)
        assert result is None

    def test_syntax_error_file(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "bad.py"
        f.write_text("def foo(:\n")
        result = analyzer.show_enclosing_scope(str(f), 1)
        assert result is None

    def test_function_scope(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("def outer():\n    def inner():\n        x = 1\n")
        result = analyzer.show_enclosing_scope(str(f), 3)
        assert result is not None
        assert "inner" in result.name

    def test_class_scope(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("class MyClass:\n    def method(self):\n        pass\n")
        result = analyzer.show_enclosing_scope(str(f), 2)
        assert result is not None
        assert "MyClass" in result.name

    def test_no_enclosing_scope(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("x = 1\ny = 2\n")
        result = analyzer.show_enclosing_scope(str(f), 1)
        assert result is None

    def test_with_filepath_value(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("def foo():\n    x = 1\n")
        result = analyzer.show_enclosing_scope(FilePath(value=str(f)), 2)
        assert result is not None


class TestFindFlow:
    def test_nonexistent_file(self):
        analyzer = SemanticScopeAnalyzer()
        result = analyzer.find_flow("/nonexistent/file.py", "x")
        assert result == []

    def test_syntax_error_file(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "bad.py"
        f.write_text("def foo(:\n")
        result = analyzer.find_flow(str(f), "x")
        assert result == []

    def test_assignment_and_usage(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("x = 1\nprint(x)\n")
        result = analyzer.find_flow(str(f), "x")
        assert len(result) == 2
        assert "Assignment" in result[0]
        assert "Usage" in result[1]

    def test_with_start_line(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("def foo():\n    x = 1\n    print(x)\n")
        result = analyzer.find_flow(str(f), "x", start_line=2)
        assert len(result) >= 1

    def test_no_variable(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("y = 1\n")
        result = analyzer.find_flow(str(f), SymbolName(value="x"))
        assert result == []

    def test_method_call(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("obj = MyClass()\nobj.do_something()\n")
        result = analyzer.find_flow(str(f), "obj")
        assert any("Mutation" in r for r in result)


class TestTraceCallChain:
    def test_single_caller(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("def foo():\n    pass\n\ndef bar():\n    foo()\n")
        result = analyzer.trace_call_chain(str(tmp_path), "foo")
        assert len(result) >= 1
        assert "foo()" in result[0]

    def test_no_callers(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("def foo():\n    pass\n")
        result = analyzer.trace_call_chain(str(tmp_path), "foo")
        assert result == []

    def test_with_symbol_name(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("def foo():\n    pass\n\ndef bar():\n    foo()\n")
        result = analyzer.trace_call_chain(str(tmp_path), SymbolName(value="foo"))
        assert len(result) >= 1

    def test_ioerror_handling(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("def foo():\n    pass\n")
        os.chmod(str(f), 0o000)
        result = analyzer.trace_call_chain(str(tmp_path), "foo")
        os.chmod(str(f), 0o644)
        assert result == []

    def test_multiple_files(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        (tmp_path / "a.py").write_text("def foo():\n    pass\n")
        (tmp_path / "b.py").write_text("def bar():\n    foo()\n")
        result = analyzer.trace_call_chain(str(tmp_path), "foo")
        assert len(result) >= 1


class TestProjectWideRename:
    def test_basic_rename(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("def old_name():\n    old_name()\n")
        count = analyzer.project_wide_rename(str(tmp_path), "old_name", "new_name")
        assert count == 1
        assert "new_name" in f.read_text()

    def test_skip_strings_and_comments(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text('"""old_name"""\n# old_name\nx = 1\n')
        count = analyzer.project_wide_rename(str(tmp_path), "old_name", "new_name")
        assert count == 0

    def test_nonexistent_dir(self):
        analyzer = SemanticScopeAnalyzer()
        count = analyzer.project_wide_rename("/nonexistent/dir", "old", "new")
        assert count == 0

    def test_with_directory_path(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("old_name = 1\n")
        count = analyzer.project_wide_rename(DirectoryPath(value=str(tmp_path)), SymbolName(value="old_name"), SymbolName(value="new_name"))
        assert count == 1

    def test_no_match(self, tmp_path):
        analyzer = SemanticScopeAnalyzer()
        f = tmp_path / "test.py"
        f.write_text("foo = 1\n")
        count = analyzer.project_wide_rename(str(tmp_path), "bar", "baz")
        assert count == 0
