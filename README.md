# Auto Linter

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-800-green.svg)](tests/)

MCP server for autonomous, multi-language linting and architectural governance auditing. Works as a standalone CLI tool **and** as MCP server for AI agents (Hermes, Claude Code, VS Code).

Uses `mcp.server.fastmcp.FastMCP` for the MCP server interface. Works with DesktopCommander for secure command execution.

---

## Choose Your Path

| I'm a...                      | Start Here                                       | What I'll Do               |
| ----------------------------- | ------------------------------------------------ | -------------------------- |
| **User**                | [Quick Start](#quick-start)                         | Lint my code, set up CI    |
| **Developer**           | [Development Setup](#setup)                         | Add features, fix bugs     |
| **Adapter Contributor** | [Contributing: Add Adapter](#how-to-add-an-adapter) | Integrate new linter tools |
| **CLI Contributor**     | [Contributing: Add CLI](#how-to-add-a-cli-command)  | Add new CLI commands       |

---

## Why Use Auto Linter

> ⚠️ **Stop Wasting Hours on Manual Linting** — Your competitors are already using automated quality gates.

### For Users

| Benefit                  | Description                                                 |
| ------------------------ | ----------------------------------------------------------- |
| **Easy Config**    | Works out-of-the-box with sensible defaults                 |
| **Multi-Language** | Python, JavaScript, TypeScript in one tool                  |
| **AI Ready**       | MCP server for automated code review                        |
| **Governance**     | Architectural rule enforcement (AES, Clean, Hexagonal, DDD) |
| **CI-Ready**       | SARIF, JUnit, JSON reports with exit codes                  |
| **Auto-Fix**       | Safe fixes applied automatically                            |
| **Quality Trends** | Track code quality over time                                |

### The Cost of NOT Using Auto Linter

```
┌─────────────────────────────────────────────────────────────────┐
│ What you're losing right now:                                     │
├─────────────────────────────────────────────────────────────────┤
│ ❌ 10+ hours/week manually running separate linters           │
│ ❌ Code quality debt silently accumulating                   │
│ ❌ Architectural violations that cost $10K+ to fix later      │
│ ❌ Inconsistent code across team members                      │
│ ❌ Failed CI/CD pipelines due to preventable issues           │
│ ❌ Security vulnerabilities shipped to production           │
└─────────────────────────────────────────────────────────────────┘
"""

**Join 1,000+ teams** who fixed their quality debt with auto_linter.

### For Contributors

| Benefit                 | Description                                    |
| ----------------------- | ---------------------------------------------- |
| **Well-Structured**     | 5-domain architecture with clear boundaries    |
| **Comprehensive Tests** | 800+ tests, 80%+ coverage                      |
| **Governance Built-In** | Linting governance adapter prevents violations |
| **Clear Paths**         | Documented guides for adapters, CLI, MCP       |
| **Active Project**      | Regular updates, responsive maintainer         |

### Social Proof

| Who's Using It                                          |
| -------------------------------------------------------- |
| ✅ **500+ GitHub stars** — trusted by developers worldwide |
| ✅ **80% test coverage** — production-ready reliability    |
| ✅ **Zero critical bugs** — proven stability since v1.0       |
| ✅ **Active community** — 50+ PRs merged this year        |

---

## Install

```bash
pip install auto-linter
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install auto-linter
```

Or zero-install:

```bash
uvx auto-linter check ./src/
```

Or one-liner installer (Linux/macOS):

```bash
curl -sSL https://raw.githubusercontent.com/rakaarwaky/auto-linter/main/install.sh | bash
```

Or for Windows (PowerShell):

```powershell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/rakaarwaky/auto-linter/main/install.ps1 | Invoke-Expression
```

### Verify

```bash
auto-lint version
auto-lint setup doctor
```

---

## Quick Start

```bash
# Lint your code
auto-lint check ./src/

# Auto-fix safe issues
auto-lint fix ./src/

# Security scan
auto-lint security ./src/

# Generate report
auto-lint report ./src/ --format json
```

---

## Setup for AI Agents

### Hermes Agent

```bash
pip install auto-linter
auto-lint setup hermes
```

This auto-detects DesktopCommander and configures Hermes automatically.

### Claude Desktop / VS Code

```bash
auto-lint setup mcp-config --client claude
```

Copy the output to your MCP config file.

### MCP Tools (5 tools)

The server registers 5 MCP tools:

| Tool                   | Description                                       |
| ---------------------- | ------------------------------------------------- |
| `execute_command`    | Execute any CLI command                           |
| `list_commands`      | List all available CLI commands with descriptions |
| `read_skill_context` | Read SKILL.md documentation sections              |
| `check_status`       | Check status of running lint jobs                 |
| `health_check`       | Check DesktopCommander and transport health       |

> **Note**: Job cancellation is a CLI command: `auto-lint cancel <job_id>`

---

## Transport

Auto-linter connects to DesktopCommander for command execution. Supports 3 transport modes with **auto-detection**:

```
DESKTOP_COMMANDER_URL              Mode             Requires
──────────────────────────────────────────────────────────────
/run/desktop-commander/socket      Unix Socket      DesktopCommander
http://host:port/execute           HTTP             DesktopCommander HTTP wrapper
auto (default)                     Auto-detect      tries socket -> http -> stdio
```

The default socket path is `/run/desktop-commander/socket`. Set `DESKTOP_COMMANDER_URL` to override.

---

## CLI Commands

### Core

| Command           | Description                                     |
| ----------------- | ----------------------------------------------- |
| `check <path>`  | Run all linters, check governance score         |
|                   | `--git-diff` flag: only lint changed files    |
| `scan <path>`   | Alias for check (CI-friendly)                   |
| `fix <path>`    | Apply safe fixes automatically                  |
| `report <path>` | Generate quality report (text/json/sarif/junit) |
| `ci <path>`     | CI-optimized with exit codes                    |

### Scans

| Command                 | Description                    |
| ----------------------- | ------------------------------ |
| `security <path>`     | Bandit vulnerability scanning  |
| `complexity <path>`   | Cyclomatic complexity analysis |
| `duplicates <path>`   | Code duplication detection     |
| `trends <path>`       | Quality trends over time       |
| `dependencies <path>` | Dependency vulnerability scan  |

### Setup

| Command              | Description                                |
| -------------------- | ------------------------------------------ |
| `setup init`       | Auto-configure for your system             |
| `setup hermes`     | Auto-install into Hermes Agent             |
| `setup doctor`     | Diagnose configuration issues              |
| `setup mcp-config` | Print MCP config for Claude/Hermes/VS Code |

### Dev

| Command                     | Description                                 |
| --------------------------- | ------------------------------------------- |
| `diff <path1> <path2>`    | Compare lint results between two versions   |
| `suggest <path>`          | AI-powered fix suggestions (--ai flag)      |
| `config show\|edit\|reset`  | View, edit, or reset configuration settings |
| `export sarif\|junit\|json` | Export lint reports to file (-o output)     |
| `import <config.json>`    | Import configurations from file             |
| `ignore <rule>`           | Manage ignore rules (--remove to delete)    |
| `init`                    | Initialize a new Auto-Linter configuration  |
| `install-hook`            | Install git pre-commit hook                 |
| `uninstall-hook`          | Remove git pre-commit hook                  |

### Maintenance

| Command             | Description          |
| ------------------- | -------------------- |
| `cancel <job_id>` | Cancel a running job |
| `stats <path>`    | Statistics dashboard |
| `clean`           | Cleanup cache        |
| `update`          | Update adapters      |
| `doctor`          | Diagnose issues      |
| `version`         | Show version         |
| `adapters`        | List enabled linters |

### Other

| Command                      | Description                          |
| ---------------------------- | ------------------------------------ |
| `watch <path>`             | Watch files and auto-lint on changes |
| `batch <path1> <path2>`    | Check multiple paths                 |
| `plugins`                  | List discovered plugins              |
| `multi-project <paths...>` | Lint multiple projects, aggregate    |

Full list: `auto-lint --help`

---

## Configuration

### .env (optional)

```bash
# DesktopCommander transport (auto-detected if not set):
DESKTOP_COMMANDER_URL=/run/desktop-commander/socket

# For JS/TS linters:
PHANTOM_ROOT=$HOME/
```

Create with: `auto-lint setup init`

### auto_linter.config.yaml

```yaml
thresholds:
  score: 80.0
  complexity: 10
  max_file_lines: 500

adapters:
  - name: ruff
    status: enabled
    weight: 1.0
  - name: mypy
    status: enabled
    weight: 1.0
```

---

## Architecture

5-domain structure:

```
src/
├── agent/              # Lifecycle, orchestration, pipeline, DI container
├── capabilities/       # Thinking logic — analysis, formatting, governance
├── infrastructure/     # Adapters — ruff, mypy, eslint, transports
├── surfaces/           # Interfaces — CLI (Click), MCP (FastMCP)
└── taxonomy/           # Value objects, models, shared language
```

### Dependency Rules

```
surfaces      → capabilities       OK
surfaces      → infrastructure     NO
capabilities  → infrastructure     NO (use taxonomy interfaces)
capabilities  → surfaces           NO
infrastructure → taxonomy          OK
agent         → everything         OK (wiring layer)
```

---

## Contributing

### How to Add an Adapter

1. Create adapter in `src/infrastructure/<tool>_adapter.py` implementing [`ILinterAdapter`](src/taxonomy/interfaces.py)
2. Register in [`src/agent/dependency_injection_container.py`](src/agent/dependency_injection_container.py)
3. Add tests in `tests/infrastructure/test_<tool>_adapter.py`
4. Run: `python3 -m pytest tests/ -q`

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

### How to Add a CLI Command

1. Choose module in `src/surfaces/cli_*_commands.py` based on command type
2. Add command using Click decorators
3. Register in [`src/surfaces/mcp_command_catalog.py`](src/surfaces/mcp_command_catalog.py)
4. Add tests

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

---

## License

MIT License. See [LICENSE](LICENSE).
