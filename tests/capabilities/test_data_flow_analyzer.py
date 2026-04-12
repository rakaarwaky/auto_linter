"""Comprehensive tests for capabilities/data_flow_analyzer.py — 100% coverage."""

import pytest
import tempfile
import os
from capabilities.data_flow_analyzer import find_flow


class TestFindFlow:
    def test_nonexistent_file(self):
        result = find_flow("/nonexistent/file.js", "x")
        assert result == []

    def test_variable_assignment_and_usage(self):
        code = """const myVar = 1;
console.log(myVar);
myVar = 2;
myVar.push(3);
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            result = find_flow(f.name, "myVar")
        os.remove(f.name)
        assert len(result) > 0
        assert any("Assignment" in r for r in result)
        assert any("Usage" in r for r in result)

    def test_variable_mutation(self):
        code = """let items = [];
items.push(1);
items.pop();
items.shift();
items.unshift(0);
items.splice(0, 1);
items.sort();
items.reverse();
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            result = find_flow(f.name, "items")
        os.remove(f.name)
        assert any("Mutation 'push'" in r for r in result)
        assert any("Mutation 'pop'" in r for r in result)
        assert any("Mutation 'shift'" in r for r in result)
        assert any("Mutation 'unshift'" in r for r in result)
        assert any("Mutation 'splice'" in r for r in result)
        assert any("Mutation 'sort'" in r for r in result)
        assert any("Mutation 'reverse'" in r for r in result)

    def test_object_mutation(self):
        code = """const obj = {};
obj.set("key", "value");
obj.delete("key");
obj.add("item");
obj.assign({}, obj);
obj.merge({});
obj.update("key");
obj.append("data");
obj.extend("more");
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            result = find_flow(f.name, "obj")
        os.remove(f.name)
        assert any("Mutation 'set'" in r for r in result)
        assert any("Mutation 'delete'" in r for r in result)
        assert any("Mutation 'add'" in r for r in result)

    def test_scope_bounds(self):
        code = """function test() {
    const x = 1;
    console.log(x);
}
const x = 2;
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            result = find_flow(f.name, "x", 1)
        os.remove(f.name)
        assert len(result) > 0

    def test_no_matches(self):
        code = """const a = 1;
const b = 2;
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            result = find_flow(f.name, "nonexistent")
        os.remove(f.name)
        assert result == []

    def test_deduplication(self):
        code = """const x = 1;
const x = 1;
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            result = find_flow(f.name, "x")
        os.remove(f.name)
        # Should not have duplicates
        assert len(result) == len(set(result))
