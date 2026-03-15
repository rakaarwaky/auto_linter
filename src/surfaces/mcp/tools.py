import json
from mcp.server.fastmcp import FastMCP
from ...bootstrap.container import Container

def register_tools(mcp: FastMCP, container: Container):
    """Bridges Capabilities to the MCP Surface (Domain 5)."""

    @mcp.tool()
    async def run_lint_check(path: str) -> str:
        """
        Run comprehensive analysis (The Governance Enforcer).
        Dynamically orchestrates all registered adapters (Python, JS, TS, etc).

        Args:
            path: Absolute path to the file or directory to lint.
        """
        report = await container.analysis_use_case.execute(path)
        results_dict = container.analysis_use_case.to_dict(report)
        return json.dumps(results_dict, indent=2)

    @mcp.tool()
    async def apply_safe_fixes(path: str) -> str:
        """
        Apply automatic safe fixes.
        Currently supports Ruff fixes for Python.

        Args:
            path: Absolute path to the file or directory to fix.
        """
        # We need ApplyFixesUseCase here. Let's add it to the container.
        return await container.fixes_use_case.execute(path)
