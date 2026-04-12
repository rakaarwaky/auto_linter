"""Comprehensive tests for config_identifier_vo.py — 100% coverage."""

import pytest
from taxonomy.config_identifier_vo import ConfigKey


class TestConfigKey:
    def test_init(self):
        ck = ConfigKey(value="thresholds.score")
        assert ck.value == "thresholds.score"

    def test_str(self):
        assert str(ConfigKey(value="adapters.0.name")) == "adapters.0.name"

    def test_hash(self):
        ck = ConfigKey(value="thresholds.score")
        assert hash(ck) == hash("thresholds.score")
        d = {ck: "found"}
        assert d[ConfigKey(value="thresholds.score")] == "found"

    def test_eq_same_type(self):
        assert ConfigKey(value="score") == ConfigKey(value="score")
        assert not (ConfigKey(value="score") == ConfigKey(value="complexity"))

    def test_eq_str(self):
        assert ConfigKey(value="score") == "score"

    def test_eq_other_type(self):
        assert ConfigKey(value="score").__eq__(42) is NotImplemented

    def test_validation_empty(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            ConfigKey(value="")

    def test_validation_whitespace(self):
        with pytest.raises(ValueError):
            ConfigKey(value="   ")

    def test_strip_whitespace(self):
        ck = ConfigKey(value="  thresholds.score  ")
        assert ck.value == "thresholds.score"

    def test_frozen(self):
        ck = ConfigKey(value="thresholds.score")
        with pytest.raises(Exception):
            ck.value = "other"

    def test_parts_single(self):
        ck = ConfigKey(value="thresholds.score")
        assert ck.parts == ["thresholds", "score"]

    def test_parts_deep(self):
        ck = ConfigKey(value="adapters.0.name")
        assert ck.parts == ["adapters", "0", "name"]

    def test_parts_single_level(self):
        ck = ConfigKey(value="project_name")
        assert ck.parts == ["project_name"]

    def test_parent_nested(self):
        ck = ConfigKey(value="thresholds.score")
        assert ck.parent == "thresholds"

    def test_parent_deep(self):
        ck = ConfigKey(value="adapters.0.name")
        assert ck.parent == "adapters.0"

    def test_parent_root(self):
        ck = ConfigKey(value="project_name")
        assert ck.parent == ""

    def test_leaf_nested(self):
        ck = ConfigKey(value="thresholds.score")
        assert ck.leaf == "score"

    def test_leaf_deep(self):
        ck = ConfigKey(value="adapters.0.name")
        assert ck.leaf == "name"

    def test_leaf_root(self):
        ck = ConfigKey(value="project_name")
        assert ck.leaf == "project_name"

    def test_model_dump(self):
        ck = ConfigKey(value="thresholds.score")
        assert ck.model_dump() == {"value": "thresholds.score"}
