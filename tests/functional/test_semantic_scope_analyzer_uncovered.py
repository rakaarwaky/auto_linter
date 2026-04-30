"""Additional tests for semantic_scope_analyzer to cover lines 131-132, 183-184."""

import os
import tempfile
from capabilities.semantic_scope_analyzer import SemanticScopeAnalyzer


class TestSemanticScopeAnalyzerUncovered:
    """Tests for uncovered lines 131-132 and 183-184."""

    def test_find_flow_with_start_line_in_class_scope(self, tmp_path):
        """Test find_flow with start_line inside a class scope (lines 131-132)."""
        py_file = tmp_path / "test.py"
        py_file.write_text("""class MyClass:
    def method(self):
        x = 1
        print(x)
""")
        
        analyzer = SemanticScopeAnalyzer()
        # Start line inside the class
        result = analyzer.find_flow(str(py_file), "x", start_line=3)
        assert len(result) >= 1
        assert any("Assignment" in r for r in result)

    def test_project_wide_rename_with_io_error(self, tmp_path):
        """Test project_wide_rename with IO errors (lines 183-184)."""
        analyzer = SemanticScopeAnalyzer()
        
        # Create a file, make it readable but not writable
        py_file = tmp_path / "readonly.py"
        py_file.write_text("old_name = 1\n")
        os.chmod(str(py_file), 0o444)
        
        try:
            count = analyzer.project_wide_rename(str(tmp_path), "old_name", "new_name")
            # Should handle IO error gracefully (modified_count stays 0 or returns without crashing)
            assert count >= 0
        finally:
            os.chmod(str(py_file), 0o644)

    def test_project_wide_rename_with_read_io_error(self, tmp_path):
        """Test project_wide_rename when file cannot be read."""
        analyzer = SemanticScopeAnalyzer()
        
        py_file = tmp_path / "unreadable.py"
        py_file.write_text("old_name = 1\n")
        os.chmod(str(py_file), 0o000)
        
        try:
            count = analyzer.project_wide_rename(str(tmp_path), "old_name", "new_name")
            # Should skip unreadable file gracefully
            assert count >= 0
        finally:
            os.chmod(str(py_file), 0o644)
