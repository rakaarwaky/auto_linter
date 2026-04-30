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
        
    # Defaults are now dynamic
    # PHANTOM_ROOT defaults to user's HOME directory
    home = os.path.expanduser("~")
    phantom_root = os.environ.get("PHANTOM_ROOT", home)
    actual_root = os.environ.get("PROJECT_ROOT", os.getcwd())
    
    if phantom_root and phantom_root in path:
        path = path.replace(phantom_root, actual_root)
        
    if path.startswith("src/") or path.startswith("./src/"):
        path = os.path.abspath(path)
        
    return path
