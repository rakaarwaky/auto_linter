"""config_setting_vo — Value objects for configuration domain (Pydantic)."""

from enum import Enum
from typing import List, Dict
from pydantic import BaseModel, ConfigDict, field_validator


class Thresholds(BaseModel):
    """Scoring thresholds."""
    model_config = ConfigDict(frozen=True)

    score: float = 80.0
    complexity: int = 10
    max_file_lines: int = 500

    @field_validator("score")
    @classmethod
    def check_score(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError(f"Score threshold must be 0.0-100.0, got {v}")
        return v

    @field_validator("complexity")
    @classmethod
    def check_complexity(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"Complexity threshold must be >= 1, got {v}")
        return v


DEFAULT_THRESHOLDS = Thresholds()


class AdapterStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    NOT_INSTALLED = "not_installed"


class AdapterEntry(BaseModel):
    """Single adapter configuration."""
    model_config = ConfigDict(frozen=True)

    name: str
    status: AdapterStatus = AdapterStatus.ENABLED
    weight: float = 1.0

    @property
    def is_active(self) -> bool:
        return self.status == AdapterStatus.ENABLED


class ProjectConfig(BaseModel):
    """Project configuration."""
    model_config = ConfigDict(frozen=True)

    project_name: str = "auto-linter"
    thresholds: Thresholds = Thresholds()
    adapters: List[AdapterEntry] = []
    ignored_paths: List[str] = ["node_modules", ".venv", "__pycache__", "dist", "build"]
    ignored_rules: List[str] = []
    governance_rules: List[Dict[str, str]] = []
    layer_map: Dict[str, str] = {}

    @classmethod
    def from_dict(cls, raw: dict) -> "ProjectConfig":
        """Parse a raw dictionary into ProjectConfig."""
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
            if isinstance(entry, str):
                adapters.append(AdapterEntry(name=entry, status=AdapterStatus.ENABLED, weight=1.0))
                continue
                
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
        project_name = raw.get("project_name", raw_project.get("name", "auto-linter"))

        # Ignored paths / rules
        ignored_paths = raw.get("ignored_paths", [])
        ignored_rules = raw.get("ignored_rules", [])

        # Governance & Layers
        governance_rules = raw.get("governance_rules", [])
        layer_map = raw.get("layer_map", {})

        return cls(
            project_name=project_name,
            thresholds=thresholds,
            adapters=adapters,
            ignored_paths=ignored_paths,
            ignored_rules=ignored_rules,
            governance_rules=governance_rules,
            layer_map=layer_map,
        )

    @classmethod
    def defaults(cls) -> "ProjectConfig":
        return cls(
            adapters=[
                AdapterEntry(name="ruff"),
                AdapterEntry(name="mypy"),
                AdapterEntry(name="bandit"),
                AdapterEntry(name="radon"),
            ]
        )
