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
    Thresholds,
    AdapterEntry,
    AdapterStatus,
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

    # Thresholds
    raw_thresh = raw.get("thresholds", {})
    thresholds = Thresholds(
        score=float(raw_thresh.get("score", 80.0)),
        complexity=int(raw_thresh.get("complexity", 10)),
        max_file_lines=int(raw_thresh.get("max_file_lines", 500)),
    )

    # Adapters — support both list of strings and list of objects
    raw_adapters = raw.get("adapters", [])
    adapters = []
    for entry in raw_adapters:
        if isinstance(entry, str):
            adapters.append(AdapterEntry(name=entry, status=AdapterStatus.ENABLED, weight=1.0))
        else:
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
    project_name = raw.get("project_name", raw.get("project", {}).get("name", "auto-linter"))

    # Ignored paths / rules
    ignored_paths = raw.get("ignored_paths", [])
    ignored_rules = raw.get("ignored_rules", [])

    return ProjectConfig(
        project_name=project_name,
        thresholds=thresholds,
        adapters=adapters,
        ignored_paths=ignored_paths,
        ignored_rules=ignored_rules,
    )


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
