"""Comprehensive tests for config_provider_error.py — 100% coverage."""

import pytest
from taxonomy.config_identifier_vo import ConfigKey
from taxonomy.lint_identifier_vo import FilePath
from taxonomy.config_provider_error import ConfigError


class TestConfigError:
    def test_init(self):
        err = ConfigError(
            key=ConfigKey(value="thresholds.score"),
            message="Invalid type"
        )
        assert err.key == ConfigKey(value="thresholds.score")
        assert err.message == "Invalid type"
        assert err.expected == ""
        assert err.actual == ""
        assert err.config_file is None

    def test_with_details(self):
        err = ConfigError(
            key=ConfigKey(value="thresholds.score"),
            message="Must be a float",
            expected="float",
            actual="str",
            config_file=FilePath(value="/path/to/config.yaml")
        )
        assert err.expected == "float"
        assert err.actual == "str"
        assert err.config_file == FilePath(value="/path/to/config.yaml")

    def test_str_without_file(self):
        err = ConfigError(
            key=ConfigKey(value="thresholds.score"),
            message="Invalid type"
        )
        assert str(err) == "Config error on 'thresholds.score': Invalid type"

    def test_str_with_file(self):
        err = ConfigError(
            key=ConfigKey(value="thresholds.score"),
            message="Invalid type",
            config_file=FilePath(value="/path/to/config.yaml")
        )
        assert str(err) == "Config error on 'thresholds.score' in /path/to/config.yaml: Invalid type"

    def test_model_dump(self):
        err = ConfigError(
            key=ConfigKey(value="thresholds.score"),
            message="Required"
        )
        dump = err.model_dump()
        assert dump["key"]["value"] == "thresholds.score"
        assert dump["message"] == "Required"

    def test_frozen(self):
        err = ConfigError(
            key=ConfigKey(value="thresholds.score"),
            message="Required"
        )
        with pytest.raises(Exception):
            err.message = "Changed"
