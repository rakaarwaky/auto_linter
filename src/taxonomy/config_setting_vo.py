"""config_setting_vo — Value objects for configuration domain (Pydantic)."""

from enum import Enum
from typing import List, Dict, Tuple
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
    def defaults(cls) -> "ProjectConfig":
        return cls(
            adapters=[
                AdapterEntry(name="ruff"),
                AdapterEntry(name="mypy"),
                AdapterEntry(name="bandit"),
                AdapterEntry(name="radon"),
            ]
        )
