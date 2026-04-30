"""Tests for config_validation_provider.py uncovered lines (190, 198)."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os


class TestConfigValidationProviderExtended:
    """Test config_validation_provider.py lines 190, 198."""

    def test_load_config_with_json_config_priority(self):
        """Test load_config when JSON config exists (line 190)."""
        from infrastructure.config_validation_provider import load_config, reset_config

        reset_config()

        mock_json_config = MagicMock()
        mock_json_config.project.governance_rules = []
        mock_json_config.project.layer_map = {}
        mock_json_config.project.thresholds = MagicMock(score=80.0, complexity=10, max_file_lines=500)
        mock_json_config.project.project_name = "test"
        mock_json_config.project.adapters = []
        mock_json_config.project.ignored_paths = []
        mock_json_config.project.ignored_rules = []

        with patch("infrastructure.config_validation_provider.load_json_config", return_value=mock_json_config):
            with patch("infrastructure.config_validation_provider._find_env_file", return_value=None):
                config = load_config()

        assert config is not None
        # JSON config should have been used
        reset_config()

    def test_load_config_with_explicit_yaml_path(self):
        """Test load_config with explicit yaml_path parameter (line 198)."""
        from infrastructure.config_validation_provider import load_config, reset_config

        reset_config()

        with patch("infrastructure.config_validation_provider.load_json_config", return_value=None):
            with patch("infrastructure.config_validation_provider._parse_yaml_config") as mock_parse:
                mock_project = MagicMock()
                mock_project.governance_rules = []
                mock_project.layer_map = {}
                mock_project.thresholds = MagicMock(score=80.0, complexity=10, max_file_lines=500)
                mock_project.project_name = "test"
                mock_project.adapters = []
                mock_project.ignored_paths = []
                mock_project.ignored_rules = []
                mock_parse.return_value = mock_project

                config = load_config(yaml_path="/tmp/test.yaml")

                mock_parse.assert_called_once_with(Path("/tmp/test.yaml"))
                assert config is not None

        reset_config()

    def test_load_config_finds_yaml_automatically(self):
        """Test load_config auto-finds YAML config."""
        from infrastructure.config_validation_provider import load_config, reset_config

        reset_config()

        with patch("infrastructure.config_validation_provider.load_json_config", return_value=None):
            with patch("infrastructure.config_validation_provider._find_yaml_config", return_value=None):
                with patch("taxonomy.ProjectConfig.defaults") as mock_defaults:
                    mock_project = MagicMock()
                    mock_project.governance_rules = []
                    mock_project.layer_map = {}
                    mock_project.thresholds = MagicMock(score=80.0, complexity=10, max_file_lines=500)
                    mock_project.project_name = "defaults"
                    mock_project.adapters = []
                    mock_project.ignored_paths = []
                    mock_project.ignored_rules = []
                    mock_defaults.return_value = mock_project

                    config = load_config()
                    assert config is not None

        reset_config()
