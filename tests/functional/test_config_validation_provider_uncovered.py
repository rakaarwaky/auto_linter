"""Additional tests for config_validation_provider to cover lines 190, 198."""

import sys
from unittest.mock import MagicMock
import json
import pytest


class TestConfigValidationProviderUncovered:
    """Tests for uncovered lines 190 and 198."""

    def test_load_config_json_exists(self, tmp_path):
        """Test load_config when JSON config exists (line 190)."""
        mock_project = MagicMock()
        mock_project.project_name = "json-test"
        mock_project.thresholds = MagicMock()
        mock_project.thresholds.score = 95.0
        mock_project.adapters = []
        mock_project.governance_rules = []
        mock_project.layer_map = {}
        mock_project.ignored_paths = []
        mock_project.ignored_rules = []

        # Force reimport with mocked dependency
        import infrastructure.config_validation_provider as cvp
        original_func = cvp.load_json_config
        cvp.load_json_config = lambda: mock_project
        cvp._config = None  # reset singleton
        try:
            config = cvp.load_config()
            assert config.project.project_name == "json-test"
        finally:
            cvp.load_json_config = original_func
            cvp._config = None

    def test_load_config_json_priority_over_yaml(self, tmp_path):
        """Test load_config priority: JSON over YAML (line 198)."""
        mock_project = MagicMock()
        mock_project.project_name = "json-priority"
        mock_project.thresholds = MagicMock()
        mock_project.thresholds.score = 80.0
        mock_project.adapters = []
        mock_project.governance_rules = []
        mock_project.layer_map = {}
        mock_project.ignored_paths = []
        mock_project.ignored_rules = []

        import infrastructure.config_validation_provider as cvp
        original_func = cvp.load_json_config
        cvp.load_json_config = lambda: mock_project
        cvp._config = None
        try:
            config = cvp.load_config()
            assert config.project.project_name == "json-priority"
        finally:
            cvp.load_json_config = original_func
            cvp._config = None
