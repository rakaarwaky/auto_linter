import os
import sys

# Dynamic PYTHONPATH: Add 'src' directory to sys.path
# This allows imports like 'from agent...' to work regardless of environment variables
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from dotenv import load_dotenv
load_dotenv()

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
# Reload triggered at 2026-04-30T12:35:00

if __name__ == "__main__":
    main()
