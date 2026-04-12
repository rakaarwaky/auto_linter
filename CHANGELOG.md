# Changelog

## 1.0.0 (2026-04-12)

### Added
- 5-domain architecture: agent, capabilities, infrastructure, surfaces, taxonomy
- Full value object (VO) system — no bare primitives for typed concepts
- 11 lint adapters: ruff, mypy, bandit, radon, pip-audit, duplicates, trends, eslint, prettier, tsc, governance
- 5 MCP tools: execute_command, list_commands, read_skill_context, check_status, health_check
- 28 CLI commands: check, scan, fix, report, security, complexity, duplicates, trends, dependencies, ci, batch, watch, version, adapters, stats, clean, update, doctor, install-hook, uninstall-hook, config, diff, export, import, ignore, init, suggest, cancel
- 4 setup commands: setup init, setup hermes, setup doctor, setup mcp-config
- Governance scoring with configurable thresholds
- SARIF and JUnit report formats
- DesktopCommander integration with 3 transports: HTTP, Unix Socket, Stdio
- Transport auto-detection (socket -> http -> stdio fallback)
- Agent pipeline orchestration: receive -> think -> act -> respond
- Job tracking with exponential backoff retry
- Lifecycle state management with health reporting
- Config validation provider with .env + YAML support
- MCP server via FastMCP (`mcp.server.fastmcp.FastMCP`)
- CLI via Click with command groups
- Git pre-commit hook install/uninstall
- File watcher for auto-lint on save
- `.env` and `.env.example` for configuration
- `install.sh` — curl-friendly installer script

### Architecture
- Uses `mcp.server.fastmcp.FastMCP` for MCP server
- Decorator-based tool registration via `@mcp.tool()`
- Tool registry split into modules: mcp_execute_command, mcp_command_catalog, mcp_job_management, mcp_health_check
- DI container in `agent/dependency_injection_container.py`
- DesktopCommander adapter with auto-detection and retry logic

### Dependencies
- mcp[cli], fastmcp, pydantic, ruff, mypy, click, watchdog, httpx, pyyaml, python-dotenv (core)
- pyre-check (optional)
