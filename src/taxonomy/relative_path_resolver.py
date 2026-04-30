import os

def normalize_path(path: str) -> str:
    """
    Standardizes paths to resolve potential environment discrepancies.
    Only performs mapping if PHANTOM_ROOT and PROJECT_ROOT are explicitly set.
    """
    if not path:
        return path
    
    # Normalize slashes first
    path = path.replace("\\", "/").replace("//", "/")
    
    phantom_root = os.environ.get("PHANTOM_ROOT")
    actual_root = os.environ.get("PROJECT_ROOT")
    
    # Only attempt replacement if BOTH are defined to avoid partial path corruption
    if phantom_root and actual_root and phantom_root in path:
        path = path.replace(phantom_root, actual_root)
    
    # Ensure it's absolute if it looks like a relative project path and we're likely in the project
    if path.startswith("src/") or path.startswith("./src/"):
        if "auto_linter" in os.getcwd() or os.path.exists(".git"):
            path = os.path.abspath(path)
             
    return path
