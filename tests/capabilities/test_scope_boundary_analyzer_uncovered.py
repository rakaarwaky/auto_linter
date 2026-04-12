"""Additional tests for scope_boundary_analyzer to cover lines 78, 90."""

import tempfile
import os
from capabilities.scope_boundary_analyzer import (
    show_enclosing_scope,
    detect_js_scope,
)


class TestScopeBoundaryAnalyzerUncovered:
    """Tests for uncovered lines 78 and 90."""

    def test_enclosing_scope_nested_classes(self):
        """Test scope boundary with nested classes (line 78)."""
        code = """class Outer {
    method1() {
        class Inner {
            innerMethod() {
                let x = 1;
            }
        }
    }
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            result = show_enclosing_scope(f.name, 5)
        os.remove(f.name)
        
        assert result is not None
        # Should show nested scope chain
        assert "Outer" in result or "Inner" in result

    def test_boundary_crossing_detection(self):
        """Test boundary crossing detection (line 90)."""
        code = """class A {
    func1() {
        let x = 1;
    }
}

class B {
    func2() {
        let y = 2;
    }
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(code)
            f.flush()
            
            # Line inside func1 should show class A -> func1
            result1 = show_enclosing_scope(f.name, 3)
            assert result1 is not None
            assert "A" in result1
            assert "func1" in result1
            
            # Line inside func2 should show class B -> func2
            result2 = show_enclosing_scope(f.name, 9)
            assert result2 is not None
            assert "B" in result2
            assert "func2" in result2
            
        os.remove(f.name)
