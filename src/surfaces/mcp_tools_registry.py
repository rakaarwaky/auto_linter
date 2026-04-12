"""
MCP Tools Registry - Bridges Capabilities to the Surface Layer.

Split into granular modules:
- mcp_desktop_client.py - _get_client, _execute_with_retry, _running_jobs
- mcp_command_catalog.py - list_commands, read_skill_context
- mcp_job_management.py - check_status (cancel_job moved to CLI)
- mcp_health_check.py   - health_check
- mcp_execute_command.py - execute_command tool
"""
from mcp.server.fastmcp import FastMCP
from agent.dependency_injection_container import Container


def register_tools(mcp: FastMCP, container: Container):
    """Bridges Capabilities to the MCP Surface (Domain 5).

    Core Tools (5 MCP):
    1. execute_command    - Universal CLI executor
    2. list_commands      - Command discovery
    3. read_skill_context - SKILL.md section reader
    4. check_status       - Job status monitoring
    5. health_check       - DesktopCommander health

    CLI only: auto-lint cancel <job_id>
    """
    # Import and delegate to split modules
    from surfaces.mcp_execute_command import register_execute_command
    from surfaces.mcp_command_catalog import register_list_commands, register_read_skill_context
    from surfaces.mcp_job_management import register_check_status
    from surfaces.mcp_health_check import register_health_check

    register_execute_command(mcp)
    register_list_commands(mcp)
    register_read_skill_context(mcp)
    register_check_status(mcp)
    register_health_check(mcp)
