import os
import sys
from mcp.server.fastmcp import FastMCP
from .tools import register_tools
from ...bootstrap.container import get_container

# PATCH: Ensure venv bin is in PATH
venv_bin = os.path.dirname(sys.executable)
current_path = os.environ.get("PATH", "")
if venv_bin not in current_path:  # pragma: no cover
    os.environ["PATH"] = venv_bin + os.path.pathsep + current_path

def main():
    """Main entry point for Auto Linter (AES Structure)."""
    mcp = FastMCP("auto-linter")
    container = get_container()

    # Register tools
    register_tools(mcp, container)

    # Run server
    mcp.run()

if __name__ == "__main__":  # pragma: no cover
    main()
