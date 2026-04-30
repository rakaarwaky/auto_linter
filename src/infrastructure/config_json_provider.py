"""config_json_provider — .auto_linter.json config loader.

Supports JSON config file alongside/ahead of YAML.
Priority: .auto_linter.json > auto_linter.config.yaml > defaults.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from taxonomy import (
    ProjectConfig,
)


def _find_json_config(start: Path | None = None) -> Optional[Path]:
    """Find .auto_linter.json config file walking up from start."""
    # Explicit env override
    explicit = os.environ.get("AUTO_LINTER_CONFIG_JSON")
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return p

    # Walk up to find .auto_linter.json
    current = start or Path.cwd()
    for _ in range(5):
        candidate = current / ".auto_linter.json"
        if candidate.is_file():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def _parse_json_config(path: Path) -> ProjectConfig:
    """Parse JSON config into ProjectConfig."""
    with open(path) as f:
        raw = json.load(f)
    return ProjectConfig.from_dict(raw)


def load_json_config(start: Path | None = None) -> Optional[ProjectConfig]:
    """Find and parse .auto_linter.json if it exists."""
    json_path = _find_json_config(start)
    if json_path:
        return _parse_json_config(json_path)
    return None


def save_json_config(config: ProjectConfig, path: Path) -> None:
    """Save a ProjectConfig as .auto_linter.json."""
    data = {
        "project_name": config.project_name,
        "thresholds": {
            "score": config.thresholds.score,
            "complexity": config.thresholds.complexity,
            "max_file_lines": config.thresholds.max_file_lines,
        },
        "adapters": [
            {"name": a.name, "status": a.status.value, "weight": a.weight}
            for a in config.adapters
        ],
        "ignored_paths": config.ignored_paths,
        "ignored_rules": config.ignored_rules,
    }
    path.write_text(json.dumps(data, indent=2) + "\n")
