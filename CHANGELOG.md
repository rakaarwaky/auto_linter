# Changelog

## 1.1.0 (2026-04-13)

### Added
- **Full system health check** — `health_check` now reports on 4 components: agent lifecycle, DesktopCommander transport, job registry, and filesystem
- **Semantic analyzers wired** — `SemanticScopeAnalyzer` and `CallChainAnalyzer` integrated into DI container (`container.semantic_analyzers`)
- **Multi-project orchestration** — moved to agent domain, uses taxonomy VOs (`ProjectResult`, `AggregatedResults`)
- **Git diff coordination** — surfaces call `container.get_git_diff()` instead of importing infrastructure directly
- **Plugin discovery coordination** — surfaces call `container.get_discovered_plugins()` and `container.get_custom_adapters()`
- **Stdio transport fallback** — DesktopCommanderAdapter now includes StdioClient as third transport option
- **SKILL.md path fixed** — `read_skill_context` resolves correct path for MCP server
- **PHANTOM_ROOT test fix** — conftest.py force-override environment variables for consistent test results
- **VS Code mypy settings** — `.vscode/settings.json` for proper src/ layout resolution

### Fixed
- **Architecture leaks eliminated** — 0 cross-layer violations (surfaces↛infra, capabilities↛infra, infra↛agent, capabilities↛agent)
- **Dead code wired and functional** — lifecycle, pipeline, multi-project, path normalization, stdio transport all operational
- **MCP import chain repaired** — `_running_jobs` moved to canonical source (`mcp_execute_command.py`)
- **Mypy type errors fixed** — null-safety for `normalize_path()`, proper `entry_points()` handling, correct return types
- **Unused imports removed** — 4 Ruff F401 violations cleaned up
- **Build artifacts removed** — `src/auto_linter.egg-info/` deleted, added to `.gitignore`
- **Entry point fixed** — `auto-lint` now uses `main()` wrapper for proper pip installation

### Removed
- `pyre-check` from core dependencies (moved to optional)
- Duplicate wiring container (`wiring_dependency_container.py`)
- Orphaned infrastructure modules (`multi_project.py`, `multi_project_aggregator.py`)

### Quality
- **1004 tests passed, 0 failed** — all tests green
- **89% code coverage**
- **Ruff: 0 violations**

## 1.0.0 (2026-04-12)

### Added
- 5-domain architecture: agent, capabilities, infrastructure, surfaces, taxonomy
- Full value object (VO) system — no bare primitives for typed concepts
- 11 lint adapters: ruff, mypy, bandit, radon, pip-audit, duplicates, trends, eslint, prettier, tsc, governance
- 5 MCP tools: execute_command, list_commands, read_skill_context, check_status, health_check
- 30 CLI commands: check, scan, fix, report, security, complexity, duplicates, trends, dependencies, ci, batch, watch, version, adapters, stats, clean, update, doctor, install-hook, uninstall-hook, config, diff, export, import, ignore, init, suggest, cancel, plugins, multi-project
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
