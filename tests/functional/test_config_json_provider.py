"""Tests for infrastructure/config_json_provider.py — boost coverage from 50%."""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch
from infrastructure.config_json_provider import (
    _find_json_config,
    _parse_json_config,
    load_json_config,
    save_json_config,
)
from taxonomy import ProjectConfig, Thresholds, AdapterEntry, AdapterStatus


# ── _find_json_config ─────────────────────────────────────────────

class TestFindJsonConfig:
    def test_env_override_valid(self, tmp_path):
        cfg = tmp_path / "override.json"
        cfg.write_text("{}")
        with patch.dict(os.environ, {"AUTO_LINTER_CONFIG_JSON": str(cfg)}):
            result = _find_json_config()
            assert result == cfg

    def test_env_override_invalid(self):
        with patch.dict(os.environ, {"AUTO_LINTER_CONFIG_JSON": "/nonexistent.json"}):
            result = _find_json_config()
            assert result is None

    def test_finds_in_current_dir(self, tmp_path):
        cfg = tmp_path / ".auto_linter.json"
        cfg.write_text("{}")
        result = _find_json_config(start=tmp_path)
        assert result == cfg

    def test_finds_in_parent_dir(self, tmp_path):
        cfg = tmp_path / ".auto_linter.json"
        cfg.write_text("{}")
        child = tmp_path / "sub" / "deep"
        child.mkdir(parents=True)
        result = _find_json_config(start=child)
        assert result == cfg

    def test_returns_none_if_not_found(self, tmp_path):
        result = _find_json_config(start=tmp_path)
        assert result is None

    def test_walks_up_to_5_levels(self, tmp_path, monkeypatch):
        # Ensure no env override interferes
        monkeypatch.delenv("AUTO_LINTER_CONFIG_JSON", raising=False)
        cfg = tmp_path / ".auto_linter.json"
        cfg.write_text("{}")
        # 4 levels deep so the 5th walk iteration reaches tmp_path
        deep = tmp_path / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        result = _find_json_config(start=deep)
        assert result == cfg

    def test_stops_at_root(self, tmp_path):
        """Walk stops when reaching filesystem root."""
        # Create a dir deep enough that we hit root
        result = _find_json_config(start=Path("/tmp"))
        # Just verify no crash
        assert result is None or isinstance(result, Path)


# ── _parse_json_config ────────────────────────────────────────────

class TestParseJsonConfig:
    def test_minimal_config(self, tmp_path):
        cfg = tmp_path / ".auto_linter.json"
        cfg.write_text("{}")
        result = _parse_json_config(cfg)
        assert result.project_name == "auto-linter"
        assert result.thresholds.score == 80.0

    def test_full_config(self, tmp_path):
        cfg = tmp_path / ".auto_linter.json"
        data = {
            "project_name": "my-project",
            "thresholds": {"score": 90, "complexity": 5, "max_file_lines": 300},
            "adapters": [
                "ruff",
                {"name": "mypy", "status": "enabled", "weight": 2.0},
                {"name": "bandit", "status": "disabled"},
            ],
            "ignored_paths": ["vendor/"],
            "ignored_rules": ["E501"],
        }
        cfg.write_text(json.dumps(data))
        result = _parse_json_config(cfg)
        assert result.project_name == "my-project"
        assert result.thresholds.score == 90.0
        assert result.thresholds.complexity == 5
        assert result.thresholds.max_file_lines == 300
        assert len(result.adapters) == 3
        assert result.adapters[0].name == "ruff"
        assert result.adapters[0].status == AdapterStatus.ENABLED
        assert result.adapters[1].weight == 2.0
        assert result.adapters[2].status == AdapterStatus.DISABLED
        assert result.ignored_paths == ["vendor/"]
        assert result.ignored_rules == ["E501"]

    def test_adapter_string_entries(self, tmp_path):
        cfg = tmp_path / ".auto_linter.json"
        cfg.write_text(json.dumps({"adapters": ["ruff", "eslint"]}))
        result = _parse_json_config(cfg)
        assert len(result.adapters) == 2
        assert all(a.status == AdapterStatus.ENABLED for a in result.adapters)

    def test_adapter_invalid_status_fallback(self, tmp_path):
        cfg = tmp_path / ".auto_linter.json"
        cfg.write_text(json.dumps({"adapters": [{"name": "x", "status": "unknown"}]}))
        result = _parse_json_config(cfg)
        assert result.adapters[0].status == AdapterStatus.ENABLED

    def test_not_installed_status(self, tmp_path):
        cfg = tmp_path / ".auto_linter.json"
        cfg.write_text(json.dumps({"adapters": [{"name": "x", "status": "not_installed"}]}))
        result = _parse_json_config(cfg)
        assert result.adapters[0].status == AdapterStatus.NOT_INSTALLED

    def test_project_name_from_nested_key(self, tmp_path):
        cfg = tmp_path / ".auto_linter.json"
        cfg.write_text(json.dumps({"project": {"name": "nested-name"}}))
        result = _parse_json_config(cfg)
        assert result.project_name == "nested-name"


# ── load_json_config ──────────────────────────────────────────────

class TestLoadJsonConfig:
    def test_returns_config_when_found(self, tmp_path):
        cfg = tmp_path / ".auto_linter.json"
        cfg.write_text(json.dumps({"project_name": "test"}))
        result = load_json_config(start=tmp_path)
        assert result is not None
        assert result.project_name == "test"

    def test_returns_none_when_not_found(self, tmp_path):
        result = load_json_config(start=tmp_path)
        assert result is None


# ── save_json_config ──────────────────────────────────────────────

class TestSaveJsonConfig:
    def test_saves_valid_json(self, tmp_path):
        config = ProjectConfig(
            project_name="saved-project",
            thresholds=Thresholds(score=75.0, complexity=8, max_file_lines=400),
            adapters=[
                AdapterEntry(name="ruff", status=AdapterStatus.ENABLED, weight=1.0),
            ],
            ignored_paths=["build/"],
            ignored_rules=["W503"],
        )
        out = tmp_path / "output.json"
        save_json_config(config, out)
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["project_name"] == "saved-project"
        assert data["thresholds"]["score"] == 75.0
        assert data["adapters"][0]["name"] == "ruff"
        assert data["ignored_paths"] == ["build/"]

    def test_roundtrip(self, tmp_path):
        """save -> load should preserve data."""
        original = ProjectConfig(
            project_name="roundtrip",
            thresholds=Thresholds(score=95.0, complexity=3, max_file_lines=200),
            adapters=[
                AdapterEntry(name="eslint", status=AdapterStatus.DISABLED, weight=0.5),
            ],
            ignored_paths=[],
            ignored_rules=[],
        )
        out = tmp_path / "roundtrip.json"
        save_json_config(original, out)
        loaded = _parse_json_config(out)
        assert loaded.project_name == original.project_name
        assert loaded.thresholds.score == original.thresholds.score
        assert loaded.adapters[0].name == original.adapters[0].name
        assert loaded.adapters[0].weight == original.adapters[0].weight
