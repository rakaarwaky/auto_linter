"""Comprehensive tests for config_setting_vo.py — 100% coverage."""

import pytest
from taxonomy.config_setting_vo import (
    Thresholds,
    AdapterStatus,
    AdapterEntry,
    ProjectConfig,
    DEFAULT_THRESHOLDS,
)


# ─── Thresholds ──────────────────────────────────────────────────────────────

class TestThresholds:
    def test_init_defaults(self):
        t = Thresholds()
        assert t.score == 80.0
        assert t.complexity == 10
        assert t.max_file_lines == 500

    def test_init_custom(self):
        t = Thresholds(score=90.0, complexity=20, max_file_lines=1000)
        assert t.score == 90.0
        assert t.complexity == 20
        assert t.max_file_lines == 1000

    def test_validate_score_boundary_low(self):
        assert Thresholds(score=0.0).score == 0.0

    def test_validate_score_boundary_high(self):
        assert Thresholds(score=100.0).score == 100.0

    def test_validate_score_below_range(self):
        with pytest.raises(ValueError, match="0.0-100.0"):
            Thresholds(score=-1.0)

    def test_validate_score_above_range(self):
        with pytest.raises(ValueError, match="0.0-100.0"):
            Thresholds(score=101.0)

    def test_validate_complexity_min(self):
        assert Thresholds(complexity=1).complexity == 1

    def test_validate_complexity_below_min(self):
        with pytest.raises(ValueError, match=">= 1"):
            Thresholds(complexity=0)

    def test_validate_complexity_high(self):
        assert Thresholds(complexity=100).complexity == 100

    def test_frozen(self):
        t = Thresholds()
        with pytest.raises(Exception):
            t.score = 90.0

    def test_model_dump(self):
        t = Thresholds(score=95.0)
        dump = t.model_dump()
        assert dump["score"] == 95.0


# ─── DEFAULT_THRESHOLDS ──────────────────────────────────────────────────────

class TestDefaultThresholds:
    def test_is_thresholds(self):
        assert isinstance(DEFAULT_THRESHOLDS, Thresholds)

    def test_default_values(self):
        assert DEFAULT_THRESHOLDS.score == 80.0
        assert DEFAULT_THRESHOLDS.complexity == 10
        assert DEFAULT_THRESHOLDS.max_file_lines == 500


# ─── AdapterStatus ───────────────────────────────────────────────────────────

class TestAdapterStatus:
    def test_enabled(self):
        assert AdapterStatus.ENABLED.value == "enabled"

    def test_disabled(self):
        assert AdapterStatus.DISABLED.value == "disabled"

    def test_not_installed(self):
        assert AdapterStatus.NOT_INSTALLED.value == "not_installed"

    def test_from_string(self):
        assert AdapterStatus("enabled") == AdapterStatus.ENABLED
        assert AdapterStatus("disabled") == AdapterStatus.DISABLED
        assert AdapterStatus("not_installed") == AdapterStatus.NOT_INSTALLED

    def test_is_str_enum(self):
        assert AdapterStatus.ENABLED == "enabled"


# ─── AdapterEntry ────────────────────────────────────────────────────────────

class TestAdapterEntry:
    def test_init_defaults(self):
        ae = AdapterEntry(name="ruff")
        assert ae.name == "ruff"
        assert ae.status == AdapterStatus.ENABLED
        assert ae.weight == 1.0

    def test_init_custom(self):
        ae = AdapterEntry(
            name="mypy",
            status=AdapterStatus.DISABLED,
            weight=2.0
        )
        assert ae.status == AdapterStatus.DISABLED
        assert ae.weight == 2.0

    def test_is_active_enabled(self):
        ae = AdapterEntry(name="ruff", status=AdapterStatus.ENABLED)
        assert ae.is_active

    def test_is_active_disabled(self):
        ae = AdapterEntry(name="ruff", status=AdapterStatus.DISABLED)
        assert not ae.is_active

    def test_is_active_not_installed(self):
        ae = AdapterEntry(name="ruff", status=AdapterStatus.NOT_INSTALLED)
        assert not ae.is_active

    def test_frozen(self):
        ae = AdapterEntry(name="ruff")
        with pytest.raises(Exception):
            ae.name = "mypy"

    def test_model_dump(self):
        ae = AdapterEntry(name="bandit")
        dump = ae.model_dump()
        assert dump["name"] == "bandit"


# ─── ProjectConfig ───────────────────────────────────────────────────────────

class TestProjectConfig:
    def test_init_defaults(self):
        pc = ProjectConfig()
        assert pc.project_name == "auto-linter"
        assert pc.thresholds == Thresholds()
        assert pc.adapters == []
        assert "node_modules" in pc.ignored_paths
        assert pc.ignored_rules == []

    def test_init_custom(self):
        pc = ProjectConfig(
            project_name="my-project",
            adapters=[AdapterEntry(name="ruff")],
            ignored_paths=["vendor"],
            ignored_rules=["E501"]
        )
        assert pc.project_name == "my-project"
        assert len(pc.adapters) == 1
        assert "vendor" in pc.ignored_paths
        assert "E501" in pc.ignored_rules

    def test_defaults_classmethod(self):
        pc = ProjectConfig.defaults()
        assert pc.project_name == "auto-linter"
        assert len(pc.adapters) == 4
        adapter_names = [a.name for a in pc.adapters]
        assert "ruff" in adapter_names
        assert "mypy" in adapter_names
        assert "bandit" in adapter_names
        assert "radon" in adapter_names

    def test_frozen(self):
        pc = ProjectConfig()
        with pytest.raises(Exception):
            pc.project_name = "changed"

    def test_model_dump(self):
        pc = ProjectConfig(project_name="test")
        dump = pc.model_dump()
        assert dump["project_name"] == "test"
