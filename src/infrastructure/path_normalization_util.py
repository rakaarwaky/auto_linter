"""infra_path_util — Path normalization for infrastructure adapters."""

import os
from typing import Optional


def normalize_path(path: Optional[str]) -> Optional[str]:
    """Normalize path: fix slashes, resolve phantom roots.

    Reads PHANTOM_ROOT and PROJECT_ROOT from environment.
    Defaults to current working directory for PROJECT_ROOT.
    """
    if not path:
        return path

    # 1. Normalize slashes and collapse separators
    # First convert to forward slashes for consistent replacement logic
    path = path.replace("\\", "/")
    # Then use normpath to collapse // and handle . or ..
    # Note: on Linux this keeps forward slashes
    path = os.path.normpath(path).replace("\\", "/")

    # 2. Handle phantom roots
    home = os.path.expanduser("~")
    phantom_root = os.environ.get("PHANTOM_ROOT", home).replace("\\", "/")
    actual_root = os.environ.get("PROJECT_ROOT", os.getcwd()).replace("\\", "/")

    if phantom_root and phantom_root in path:
        path = path.replace(phantom_root, actual_root)

    # 3. Handle src/ pathing only if it's NOT explicitly relative or absolute
    if path.startswith("src/"):
        # Check if it exists in current dir
        if not os.path.exists(path):
             # Try to find it relative to project root if provided
             project_root = os.environ.get("PROJECT_ROOT")
             if project_root:
                 candidate = os.path.join(project_root, path)
                 if os.path.exists(candidate):
                     return os.path.abspath(candidate).replace("\\", "/")
        
        if os.path.exists(path):
            return os.path.abspath(path).replace("\\", "/")

    return path
