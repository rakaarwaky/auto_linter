"""config_validation_provider — .env + YAML config loader, single source of truth."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml  # type: ignore[import-untyped]
from dotenv import load_dotenv

from taxonomy import (
    ProjectConfig,
    Thresholds,
    AdapterEntry,
    AdapterStatus,
)
from infrastructure.config_json_provider import load_json_config


class AppConfig:
    """Unified configuration — transport, paths, and project settings."""

    def __init__(
        self,
        # ── Transport (.env) ──
        desktop_commander_url: str = "auto",
        desktop_commander_timeout: float = 300.0,
        # ── Paths (.env) ──
        phantom_root: str = "/home/raka/src/",
        project_root: str = "",
        # ── Project (YAML) ──
        project: ProjectConfig | None = None,
    ):
        self.desktop_commander_url = desktop_commander_url
        self.desktop_commander_timeout = desktop_commander_timeout
        self.phantom_root = phantom_root
        self.project_root = project_root or str(
            Path(__file__).resolve().parent.parent / "src"
        )
        self.project = project or ProjectConfig.defaults()

    # ── Thresholds shortcut ──

    @property
    def thresholds(self) -> Thresholds:
        return self.project.thresholds

    # ── Adapter helpers ──

    def adapter_status(self, name: str) -> AdapterStatus:
        """Get status for a named adapter."""
        for entry in self.project.adapters:
            if entry.name == name:
                return entry.status
        return AdapterStatus.NOT_INSTALLED

    def is_adapter_enabled(self, name: str) -> bool:
        return self.adapter_status(name) == AdapterStatus.ENABLED

    def active_adapters(self) -> list[str]:
        """Names of enabled adapters."""
        return [e.name for e in self.project.adapters if e.is_active]

    def __repr__(self) -> str:
        return (
            f"AppConfig(dc_url={self.desktop_commander_url!r}, "
            f"phantom={self.phantom_root!r}, "
            f"adapters={self.active_adapters()})"
        )


# ── Loaders ──


def _find_env_file(start: Path | None = None) -> Optional[Path]:
    """Walk up from start to find .env file."""
    current = start or Path.cwd()
    for _ in range(5):
        candidate = current / ".env"
        if candidate.is_file():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def _find_yaml_config(start: Path | None = None) -> Optional[Path]:
    """Find YAML config: AUTO_LINTER_CONFIG env → auto_linter.config.yaml."""
    # Explicit env override
    explicit = os.environ.get("AUTO_LINTER_CONFIG")
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return p

    # Walk up to find auto_linter.config.yaml
    current = start or Path.cwd()
    for _ in range(5):
        candidate = current / "auto_linter.config.yaml"
        if candidate.is_file():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def _parse_yaml_config(path: Path) -> ProjectConfig:
    """Parse YAML config into ProjectConfig."""
    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    # Thresholds
    raw_thresh = raw.get("thresholds", {})
    thresholds = Thresholds(
        score=float(raw_thresh.get("score", 80.0)),
        complexity=int(raw_thresh.get("complexity", 10)),
        max_file_lines=int(raw_thresh.get("max_file_lines", 500)),
    )

    # Adapters
    raw_adapters = raw.get("adapters", [])
    adapters = []
    for entry in raw_adapters:
        status_str = entry.get("status", "enabled")
        status = AdapterStatus(status_str) if status_str in (
            "enabled", "disabled", "not_installed"
        ) else AdapterStatus.ENABLED
        adapters.append(
            AdapterEntry(
                name=entry["name"],
                status=status,
                weight=float(entry.get("weight", 1.0)),
            )
        )

    # Project name
    raw_project = raw.get("project", {})
    project_name = raw_project.get("name", "auto-linter")

    # Ignored paths / rules
    ignored_paths = raw.get("ignored_paths", [])
    ignored_rules = raw.get("ignored_rules", [])

    # Governance & Layers
    governance_rules = raw.get("governance_rules", [])
    layer_map = raw.get("layer_map", {})

    return ProjectConfig(
        project_name=project_name,
        thresholds=thresholds,
        adapters=adapters,
        ignored_paths=ignored_paths,
        ignored_rules=ignored_rules,
        governance_rules=governance_rules,
        layer_map=layer_map,
    )


# ── Singleton ──

_config: Optional[AppConfig] = None


def load_config(
    env_path: Path | str | None = None,
    yaml_path: Path | str | None = None,
) -> AppConfig:
    """Load or reload configuration. Returns AppConfig.

    Args:
        env_path:  Explicit .env path. None = auto-find.
        yaml_path: Explicit YAML path. None = auto-find.
    """
    global _config

    # 1. Load .env
    if env_path:
        load_dotenv(Path(env_path), override=False)
    else:
        found_env = _find_env_file()
        if found_env:
            load_dotenv(found_env, override=False)

    # 2. Load config — JSON takes priority over YAML
    json_config = load_json_config()
    if json_config:
        yaml_config = json_config
    elif yaml_path:
        yaml_config = _parse_yaml_config(Path(yaml_path))
    else:
        found_yaml = _find_yaml_config()
        if found_yaml:
            yaml_config = _parse_yaml_config(found_yaml)
        else:
            yaml_config = ProjectConfig.defaults()

    # 3. Build AppConfig from env + YAML
    _config = AppConfig(
        desktop_commander_url=os.environ.get(
            "DESKTOP_COMMANDER_URL", "auto",
        ),
        desktop_commander_timeout=float(
            os.environ.get("DESKTOP_COMMANDER_TIMEOUT", "300")
        ),
        phantom_root=os.environ.get("PHANTOM_ROOT", "/home/raka/src/"),
        project_root=os.environ.get("PROJECT_ROOT", ""),
        project=yaml_config,
    )
    return _config


def get_config() -> AppConfig:
    """Get the global config. Auto-loads on first call."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """Reset singleton (for testing)."""
    global _config
    _config = None
