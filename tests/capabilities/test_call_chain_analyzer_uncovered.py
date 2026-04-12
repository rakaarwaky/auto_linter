"""Additional tests for call_chain_analyzer to cover lines 93-94."""

import os
import tempfile
from capabilities.call_chain_analyzer import CallChainAnalyzer


class TestCallChainAnalyzerUncovered:
    """Tests for uncovered lines 93-94 (OS error during file reading)."""

    def test_trace_call_chain_os_error(self):
        """Test call chain with OS error during file read."""
        analyzer = CallChainAnalyzer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.js")
            with open(test_file, "w") as f:
                f.write("myFunc();\n")
            
            # Make file unreadable
            os.chmod(test_file, 0o000)
            try:
                result = analyzer.trace_call_chain(tmpdir, "myFunc")
                # Should skip the unreadable file gracefully
                assert result == []
            finally:
                os.chmod(test_file, 0o644)
