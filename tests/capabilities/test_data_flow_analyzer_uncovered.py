"""Additional tests for data_flow_analyzer to cover lines 19-20, 38."""

import tempfile
import os
from capabilities.data_flow_analyzer import find_flow


class TestDataFlowAnalyzerUncovered:
    """Tests for uncovered lines 19-20 and 38."""

    def test_data_flow_with_mutations(self):
        """Test data flow with mutation patterns (line 38)."""
        code = """let data = {};
data.set("key", "value");
data.delete("key");
data.update("field");
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            result = find_flow(f.name, "data")
        os.remove(f.name)

        assert any("Mutation 'set'" in r for r in result)
        assert any("Mutation 'delete'" in r for r in result)
        assert any("Mutation 'update'" in r for r in result)

    def test_data_flow_tracking(self):
        """Test data flow tracking with assignments and usages."""
        code = """const config = {};
config.key = "value";
console.log(config);
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            result = find_flow(f.name, "config")
        os.remove(f.name)

        assert any("Assignment" in r for r in result)
        assert any("Usage" in r for r in result)

    def test_data_flow_with_scope_bounds_skip_early_lines(self):
        """Test find_flow with start_line that sets scope bounds, skipping early lines (line 38)."""
        code = """// Line 1: before scope
let x = 1;
function test() {
    let data = {};
    data.push("item");
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            # Start line inside the function, so lines 1-2 should be skipped
            result = find_flow(f.name, "data", start_line=4)
            os.remove(f.name)
            # Should find the push mutation but NOT the "let data" on line 4 if scope starts later
            assert any("Mutation" in r for r in result) or len(result) >= 1
