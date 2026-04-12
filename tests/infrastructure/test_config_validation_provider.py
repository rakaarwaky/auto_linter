"""Tests for config validation provider."""
from unittest.mock import patch
from src.infrastructure.config_validation_provider import (
    AppConfig, _find_env_file, _find_yaml_config, _parse_yaml_config,
    load_config, get_config, reset_config
)
from taxonomy import ProjectConfig, Thresholds, AdapterEntry, AdapterStatus


class TestAppConfig:
    def test_defaults(self):
        config = AppConfig()
        assert config.desktop_commander_url == "auto"
        assert config.desktop_commander_timeout == 300.0
        assert config.phantom_root == "/home/raka/src/"

    def test_custom_values(self):
        project = ProjectConfig.defaults()
        config = AppConfig(
            desktop_commander_url="http://localhost:8080",
            desktop_commander_timeout=60.0,
            phantom_root="/custom/",
            project_root="/custom/project",
            project=project,
        )
        assert config.desktop_commander_url == "http://localhost:8080"
        assert config.desktop_commander_timeout == 60.0
        assert config.phantom_root == "/custom/"
        assert config.project_root == "/custom/project"

    def test_thresholds(self):
        thresholds = Thresholds(score=90.0, complexity=5, max_file_lines=300)
        project = ProjectConfig(
            project_name="test",
            thresholds=thresholds,
            adapters=[],
        )
        config = AppConfig(project=project)
        assert config.thresholds.score == 90.0

    def test_adapter_status_enabled(self):
        adapter = AdapterEntry(name="ruff")
        project = ProjectConfig(
            project_name="test",
            adapters=[adapter],
        )
        config = AppConfig(project=project)
        assert config.adapter_status("ruff") == AdapterStatus.ENABLED
        assert config.is_adapter_enabled("ruff") is True

    def test_adapter_status_disabled(self):
        adapter = AdapterEntry(name="ruff", status=AdapterStatus.DISABLED)
        project = ProjectConfig(
            project_name="test",
            adapters=[adapter],
        )
        config = AppConfig(project=project)
        assert config.adapter_status("ruff") == AdapterStatus.DISABLED
        assert config.is_adapter_enabled("ruff") is False

    def test_adapter_status_not_found(self):
        config = AppConfig()
        assert config.is_adapter_enabled("nonexistent") is False

    def test_active_adapters(self):
        adapters = [
            AdapterEntry(name="ruff"),
            AdapterEntry(name="mypy", status=AdapterStatus.DISABLED),
        ]
        project = ProjectConfig(
            project_name="test",
            adapters=adapters,
        )
        config = AppConfig(project=project)
        assert "ruff" in config.active_adapters()
        assert "mypy" not in config.active_adapters()

    def test_repr(self):
        config = AppConfig(
            desktop_commander_url="http://localhost:8080",
            phantom_root="/custom/",
        )
        r = repr(config)
        assert "http://localhost:8080" in r
        assert "/custom/" in r


class TestFindEnvFile:
    def test_find_env_in_current_dir(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST=1")
        result = _find_env_file(tmp_path)
        assert result == env_file

    def test_find_env_in_parent_dir(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST=1")
        sub = tmp_path / "sub"
        sub.mkdir()
        result = _find_env_file(sub)
        assert result == env_file

    def test_no_env_file(self, tmp_path):
        result = _find_env_file(tmp_path)
        assert result is None


class TestFindYamlConfig:
    def test_find_yaml_in_current_dir(self, tmp_path):
        yaml_file = tmp_path / "auto_linter.config.yaml"
        yaml_file.write_text("project:\n  name: test\n")
        result = _find_yaml_config(tmp_path)
        assert result == yaml_file

    def test_find_yaml_in_parent_dir(self, tmp_path):
        yaml_file = tmp_path / "auto_linter.config.yaml"
        yaml_file.write_text("project:\n  name: test\n")
        sub = tmp_path / "sub"
        sub.mkdir()
        result = _find_yaml_config(sub)
        assert result == yaml_file

    def test_explicit_env_override(self, tmp_path):
        yaml_file = tmp_path / "custom.yaml"
        yaml_file.write_text("project:\n  name: test\n")
        with patch.dict("os.environ", {"AUTO_LINTER_CONFIG": str(yaml_file)}):
            result = _find_yaml_config(tmp_path)
            assert result == yaml_file

    def test_explicit_env_not_found(self, tmp_path):
        with patch.dict("os.environ", {"AUTO_LINTER_CONFIG": "/nonexistent.yaml"}):
            result = _find_yaml_config(tmp_path)
            # Falls through to normal search
            assert result is None

    def test_no_yaml_file(self, tmp_path):
        result = _find_yaml_config(tmp_path)
        assert result is None


class TestParseYamlConfig:
    def test_parse_basic(self, tmp_path):
        yaml_file = tmp_path / "auto_linter.config.yaml"
        yaml_file.write_text("""
project:
  name: my-project
thresholds:
  score: 90.0
  complexity: 5
  max_file_lines: 300
adapters:
  - name: ruff
    status: enabled
    weight: 1.0
""")
        config = _parse_yaml_config(yaml_file)
        assert config.project_name == "my-project"
        assert config.thresholds.score == 90.0
        assert len(config.adapters) == 1
        assert config.adapters[0].name == "ruff"

    def test_parse_defaults(self, tmp_path):
        yaml_file = tmp_path / "auto_linter.config.yaml"
        yaml_file.write_text("{}")
        config = _parse_yaml_config(yaml_file)
        assert config.thresholds.score == 80.0

    def test_parse_disabled_adapter(self, tmp_path):
        yaml_file = tmp_path / "auto_linter.config.yaml"
        yaml_file.write_text("""
adapters:
  - name: mypy
    status: disabled
    weight: 0.5
""")
        config = _parse_yaml_config(yaml_file)
        assert config.adapters[0].status == AdapterStatus.DISABLED

    def test_parse_with_ignored_paths(self, tmp_path):
        yaml_file = tmp_path / "auto_linter.config.yaml"
        yaml_file.write_text("""
project:
  name: test
ignored_paths:
  - tests/
  - vendor/
ignored_rules:
  - E501
governance_rules:
  - rule: "No direct imports from infrastructure"
layer_map:
  surfaces: "1"
  capabilities: "2"
  infrastructure: "3"
  taxonomy: "0"
""")
        config = _parse_yaml_config(yaml_file)
        assert "tests/" in config.ignored_paths
        assert "E501" in config.ignored_rules


class TestLoadConfig:
    def setup_method(self):
        reset_config()

    def teardown_method(self):
        reset_config()

    def test_load_config_defaults(self, tmp_path):
        config = load_config()
        assert config.desktop_commander_url == "auto"
        assert config.desktop_commander_timeout == 300.0

    def test_load_config_with_explicit_env(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("DESKTOP_COMMANDER_URL=http://localhost:9090\n")
        config = load_config(env_path=env_file)
        assert config.desktop_commander_url == "http://localhost:9090"

    def test_load_config_with_explicit_yaml(self, tmp_path):
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("project:\n  name: test\n")
        config = load_config(yaml_path=yaml_file)
        assert config.project.project_name == "test"

    def test_load_config_singleton(self, tmp_path):
        reset_config()
        config1 = load_config()
        config2 = get_config()
        assert config1 is config2


class TestGetConfig:
    def setup_method(self):
        reset_config()

    def teardown_method(self):
        reset_config()

    def test_get_config_auto_loads(self):
        config = get_config()
        assert isinstance(config, AppConfig)

    def test_get_config_returns_singleton(self):
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2


class TestResetConfig:
    def test_reset_config(self):
        reset_config()
        import infrastructure.config_validation_provider as cvp
        assert cvp._config is None
