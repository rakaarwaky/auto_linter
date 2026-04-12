# Product Requirements Document (PRD)

## Auto Linter MCP Server v1.0.0

---

## 1. Product Overview

**Name**: Auto Linter
**Type**: MCP Server + CLI Tool
**Version**: 1.0.0
**License**: MIT
**Language**: Python >= 3.12

Auto Linter is an autonomous multi-language linting, type-checking, and
architectural governance auditing tool. It runs as both an MCP server
(for AI agent integration) and a standalone CLI tool (for human use).

Uses `mcp.server.fastmcp.FastMCP` for the MCP server interface.
Connects to DesktopCommander for secure command execution.

---

## 2. Problem Statement

Software projects accumulate quality debt silently. Developers lack:

- Automated pre-commit quality gates that run without configuration
- Architectural enforcement that prevents cross-layer violations
- Unified interface across multiple linters (Ruff, MyPy, Bandit, ESLint...)
- Both human-accessible CLI and AI-agent-accessible MCP tools from one codebase
- Easy setup for community/open-source distribution

Auto Linter solves all five.

---

## 3. Target Users

| User            | Interface           | Use Case                                                 |
| --------------- | ------------------- | -------------------------------------------------------- |
| AI Agents       | MCP tools (5 tools) | Automated code review, pre-commit checks, CI integration |
| Developers      | CLI (30+ commands)  | Local development, watch mode, git hooks                 |
| CI/CD Pipelines | CLI + exit codes    | Quality gates, SARIF/JUnit reports                       |
| Community       | pip install + setup | Easy install, works immediately                          |
| Contributors    | GitHub + PRs        | Adapters, CLI commands, MCP tools                        |

---

## 4. Functional Requirements

### 4.1 Core Linting Engine

| ID     | Requirement                                    | Status |
| ------ | ---------------------------------------------- | ------ |
| FR-001 | Run Ruff linting on Python files               | Done   |
| FR-002 | Run MyPy type checking on Python files         | Done   |
| FR-003 | Run Bandit security scanning on Python files   | Done   |
| FR-004 | Run ESLint on JavaScript/TypeScript files      | Done   |
| FR-005 | Run Prettier formatting on JS/TS files         | Done   |
| FR-006 | Run TSC type checking on TypeScript files      | Done   |
| FR-007 | Run Radon complexity analysis on Python files  | Done   |
| FR-008 | Run pip-audit dependency vulnerability scan    | Done   |
| FR-009 | Detect oversized files (>500 lines)            | Done   |
| FR-010 | Track quality trends over time                 | Done   |
| FR-011 | Apply safe auto-fixes (Ruff, ESLint, Prettier) | Done   |
| FR-012 | Architectural governance (AES layer rules)     | Done   |

### 4.2 Report Formats

| ID     | Format                             | Status |
| ------ | ---------------------------------- | ------ |
| FR-020 | Text (human-readable)              | Done   |
| FR-021 | JSON (machine-readable)            | Done   |
| FR-022 | SARIF 2.1.0 (GitHub Code Scanning) | Done   |
| FR-023 | JUnit XML (Jenkins/CI)             | Done   |

### 4.3 Integration

| ID     | Requirement                                     | Status |
| ------ | ----------------------------------------------- | ------ |
| FR-030 | MCP server via FastMCP (`mcp.server.fastmcp`)   | Done   |
| FR-031 | CLI via Click                                   | Done   |
| FR-032 | DesktopCommander integration (socket/HTTP/auto) | Done   |
| FR-033 | Git pre-commit hook install/uninstall           | Done   |
| FR-034 | File watcher for auto-lint on save              | Done   |
| FR-035 | Auto-detect transport (socket -> http -> stdio) | Done   |
| FR-036 | Community setup (setup init/hermes/doctor)      | Done   |
| FR-037 | pip install + uvx support                       | Done   |
| FR-038 | curl installer script                           | Done   |

### 4.4 Semantic Analysis (Enrichment)

| ID     | Requirement                                            | Status |
| ------ | ------------------------------------------------------ | ------ |
| FR-040 | Show enclosing scope (function/class) for violations   | Done   |
| FR-041 | Trace call chains across project                       | Done   |
| FR-042 | Track variable flow within scope                       | Done   |
| FR-043 | Project-wide symbol rename                             | Done   |
| FR-044 | Generate naming variants (snake_case, camelCase, etc.) | Done   |

---

## 5. Non-Functional Requirements

| ID      | Requirement                   | Target  | Current |
| ------- | ----------------------------- | ------- | ------- |
| NFR-001 | Test coverage                 | >= 80%  | 800     |
| NFR-002 | All tests passing             | 100%    | 800/800 |
| NFR-003 | Startup time (MCP server)     | < 2s    | ~1s     |
| NFR-004 | Single-file scan time         | < 5s    | ~2s     |
| NFR-005 | Full project scan (100 files) | < 30s   | ~10s    |
| NFR-006 | Python version                | >= 3.12 | 3.12+   |
| NFR-007 | Max directory depth           | <= 5    | 5       |

---

## 6. Architecture

### 6.1 Domain Model (5 Domains)

```
src/
  agent/           -- Lifecycle, orchestration, pipeline, DI container
  capabilities/    -- Thinking logic: analysis, formatting, governance
  infrastructure/  -- Adapters: ruff, mypy, eslint, transports
  surfaces/        -- Interfaces: CLI (Click), MCP (FastMCP)
  taxonomy/        -- Shared types: value objects, models, errors
```

### 6.2 Dependency Rules

```
surfaces     -> capabilities       ALLOWED
surfaces     -> infrastructure     FORBIDDEN
capabilities -> infrastructure     FORBIDDEN (use taxonomy interfaces)
capabilities -> surfaces           FORBIDDEN
infrastructure -> taxonomy         ALLOWED
agent        -> *                  ALLOWED (wiring layer)
```

### 6.3 MCP Server Architecture

Uses `mcp.server.fastmcp.FastMCP` with register-function based tool registration.
Tool registry is split into granular modules:

```
mcp_server_entry.py     -- creates FastMCP, registers tools
mcp_tools_registry.py   -- bridges modules, calls register_*()
mcp_execute_command.py  -- execute_command tool (DesktopCommander delegation)
mcp_command_catalog.py  -- list_commands + read_skill_context
mcp_job_management.py   -- check_status (cancel moved to CLI: auto-lint cancel)
mcp_health_check.py     -- health_check
mcp_desktop_client.py   -- DesktopCommander adapter client
```

---

## 7. MCP Interface (5 Tools)

| Tool                            | Purpose                                      |
| ------------------------------- | -------------------------------------------- |
| `execute_command(action, args)` | Execute any CLI command via DesktopCommander |
| `list_commands(domain)`         | Discover available CLI commands              |
| `read_skill_context(section)`   | Read SKILL.md documentation                  |
| `check_status(job_id)`          | Check status of running lint job             |
| `health_check()`                | Check DesktopCommander and transport health  |

> **Note**: Job cancellation is a CLI command: `auto-lint cancel <job_id>`

---

## 8. CLI Interface (30 Commands)

| Category    | Commands                                                                          |
| ----------- | --------------------------------------------------------------------------------- |
| Core        | check, scan, fix, report, ci, version, adapters, security, cancel                 |
| Analysis    | complexity, duplicates, trends, dependencies, batch                               |
| Dev         | diff, suggest, ignore, config, export, import, init, install-hook, uninstall-hook |
| Setup       | setup init, setup hermes, setup doctor, setup mcp-config                          |
| Maintenance | stats, clean, update, doctor                                                      |
| Other       | watch, plugins, multi-project                                                     |

---

## 9. DesktopCommander Integration

### Transport Auto-Detection

```
DESKTOP_COMMANDER_URL              Mode             Requires
──────────────────────────────────────────────────────────────
/run/desktop-commander/socket      Unix Socket      DesktopCommander
http://host:port/execute           HTTP             HTTP wrapper
auto (default)                     Auto-detect      tries socket -> http -> stdio
```

Default socket path: `/run/desktop-commander/socket`

### Environment Variables

| Variable                 | Default                         | Description        |
| ------------------------ | ------------------------------- | ------------------ |
| `DESKTOP_COMMANDER_URL`  | `/run/desktop-commander/socket` | Transport endpoint |
| `DESKTOP_COMMANDER_PORT` | `24680`                         | HTTP wrapper port  |
| `PHANTOM_ROOT`           | `$HOME/`                        | JS/TS linter root  |

---

## 10. Dependencies

| Package       | Type     | Purpose                        |
| ------------- | -------- | ------------------------------ |
| mcp[cli]      | Core     | MCP protocol library           |
| fastmcp       | Core     | FastMCP server framework       |
| pydantic      | Core     | Data validation                |
| ruff          | Core     | Python linter/formatter        |
| mypy          | Core     | Python type checker            |
| click         | Core     | CLI framework                  |
| watchdog      | Core     | File system watcher            |
| httpx         | Core     | HTTP client for DC integration |
| pyyaml        | Core     | YAML config parsing            |
| python-dotenv | Core     | .env file loading              |
| pyre-check    | Optional | Python type checker (alt)      |

---

## 11. Constraints

- Python only (no Go/Rust rewrite)
- Free models only (no paid API dependencies)
- DesktopCommander is required for MCP tool execution
- No database required (file-based history only)
- FastMCP for MCP server (decorator-based registration)
- Platform Linux Windows Mac
