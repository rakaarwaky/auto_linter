import os

def normalize_path(path: str) -> str:
    """
    Standardizes paths to resolve 'phantom path' discrepancies between 
    the persistent environment and the linter's execution context.
    """
    if not path:
        return path
    
    # Normalize slashes
    path = path.replace("\\", "/").replace("//", "/")
    
    # Specific mapping for the known phantom root, can be overridden by env vars
    phantom_root = os.environ.get("PHANTOM_ROOT", "/home/raka/src/")
    actual_root = os.environ.get("PROJECT_ROOT", "/persistent/home/raka/mcp-servers/auto_linter/src/")
    
    if phantom_root in path:
        path = path.replace(phantom_root, actual_root)
    
    # Ensure it's absolute if it looks like a project path
    if path.startswith("src/") or path.startswith("./src/"):
        cwd = os.getcwd()
        if "auto_linter" in cwd:
             # We are likely at project root
             path = os.path.abspath(path)
             
    return path
