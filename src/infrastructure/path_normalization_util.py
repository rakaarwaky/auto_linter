"""infra_path_util — Path normalization for infrastructure adapters."""

import os
from typing import Optional


def normalize_path(path: Optional[str]) -> Optional[str]:
    """Normalize path: fix slashes, resolve phantom roots.

    Reads PHANTOM_ROOT and PROJECT_ROOT from environment.
    These are set by .env loading (config_provider) or manually.
    """
    if not path:
        return path
    path = path.replace("\\", "/").replace("//", "/")
    phantom_root = os.environ.get("PHANTOM_ROOT", "/home/raka/src/")
    actual_root = os.environ.get(
        "PROJECT_ROOT",
        "/persistent/home/raka/mcp-servers/auto_linter/src/",
    )
    if phantom_root in path:
        path = path.replace(phantom_root, actual_root)
    if path.startswith("src/") or path.startswith("./src/"):
        cwd = os.getcwd()
        if "auto_linter" in cwd:
            path = os.path.abspath(path)
    return path
