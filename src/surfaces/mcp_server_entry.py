import os
import sys
from mcp.server.fastmcp import FastMCP
from agent.dependency_injection_container import get_container
from surfaces.mcp_tools_registry import register_tools

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
