"""Additional tests for javascript_scope_detector to cover line 34."""

from infrastructure.javascript_scope_detector import show_enclosing_scope


class TestJSScopeDetectorUncovered:
    """Test scope detection when file doesn't exist (line 34)."""

    def test_file_does_not_exist(self):
        """Returns None when file doesn't exist."""
        result = show_enclosing_scope("/nonexistent/file.js", 1)
        assert result is None

    def test_file_cannot_be_read(self):
        """Returns None when file cannot be read (OSError)."""
        import tempfile
        import os
        
        # Create a file and make it unreadable
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("function test() {\n}\n")
            f.flush()
            path = f.name
        
        try:
            os.chmod(path, 0o000)
            result = show_enclosing_scope(path, 1)
            assert result is None
        finally:
            os.chmod(path, 0o644)
            os.unlink(path)
