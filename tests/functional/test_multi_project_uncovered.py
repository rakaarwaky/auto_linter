"""Additional tests for multi_project_orchestrator to cover lines 36-37."""

import json
import tempfile
import os
from pathlib import Path
from agent.multi_project_orchestrator import load_multi_project_config


class TestMultiProjectOrchestratorUncovered:
    """Tests for uncovered lines 36-37 (config loading from file)."""

    def test_load_multi_project_config_from_file(self):
        """Test multi-project config loading from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".auto_linter.json"
            config_path.write_text(json.dumps({
                "multi_project_paths": ["/project/a", "/project/b", "/project/c"]
            }))
            
            result = load_multi_project_config(config_path)
            assert result == ["/project/a", "/project/b", "/project/c"]

    def test_load_multi_project_config_invalid_json(self):
        """Test config loading with invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".auto_linter.json"
            config_path.write_text("not valid json {{{")
            
            result = load_multi_project_config(config_path)
            # Should return empty list on parse error
            assert result == []

    def test_load_multi_project_config_missing_key(self):
        """Test config loading when key is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".auto_linter.json"
            config_path.write_text(json.dumps({"other_key": "value"}))
            
            result = load_multi_project_config(config_path)
            assert result == []
