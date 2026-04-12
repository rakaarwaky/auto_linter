---
name: auto-linter
description: MCP server for autonomous linting and governance auditing.
version: 1.0.0
---
# Auto Linter Skill

>  **The Ultimate Linting Power-Up for AI Agents** — Used by top-performing teams.

MCP server that provides autonomous, multi-language linting and architectural governance auditing. Works as standalone CLI tool and as MCP server for AI agents via FastMCP (`mcp.server.fastmcp.FastMCP`).

## Why AI Agents Choose auto_linter

| Feature                | Benefit for Agent                         |
| ---------------------- | ----------------------------------------- |
| **5 MCP Tools**  | Complete control via execute_command      |
| **Job Tracking** | Never lose track of lint progress         |
| **Auto-Fix**     | Automatically fix 80% of issues           |
| **Retry Logic**  | Built-in resilience for failures          |
| **Governance**   | Enforce architectural rules automatically |

## Install

```bash
pip install auto-linter
```

For Hermes users: `auto-lint setup hermes`

## MCP Tools (5 tools)

### `execute_command(action: str, args: dict | None)`

Execute any CLI command via DesktopCommander pipeline. This is the primary tool.

```json
{"action": "check", "args": {"path": "./src/"}}
{"action": "fix", "args": {"path": "./src/"}}
{"action": "report", "args": {"path": "./src/", "format": "json"}}
{"action": "security", "args": {"path": "./src/"}}
{"action": "complexity", "args": {"path": "./src/"}}
```

All CLI commands are accessible through this tool.

### `list_commands(domain: str | None)`

List all available CLI commands with descriptions and examples.

```json
{ "domain": null }
```

Returns: `{"check": {"description": "...", "example_usage": "auto-lint check /path"}, ...}`

### `read_skill_context(section: str | None)`

Read SKILL.md documentation sections.

```json
{ "section": "mcp tools" }
```

### `check_status(job_id: str | None)`

Check status of running lint jobs.

```json
{ "job_id": "abc12345" }
```

> **Note**: To cancel a job, use CLI: `auto-lint cancel <job_id>`

### `health_check()`

Check DesktopCommander and transport health status.

Returns: `{"status": "...", "protocol": "...", ...}`

## Recommended Agent Workflow

```
1. list_commands()              — discover available commands
2. execute_command("check", {"path": "./src/"})  — run lint
3. execute_command("fix", {"path": "./src/"})    — auto-fix
4. execute_command("check", {"path": "./src/"})  — verify
```

## CLI Commands Reference

### Core

| Command                                   | Description                                     |
| ----------------------------------------- | ----------------------------------------------- |
| `auto-lint check <path>`                | Run all linters, check governance score         |
| `auto-lint scan <path>`                 | Alias for check (CI-friendly)                   |
| `auto-lint fix <path>`                  | Apply safe fixes automatically                  |
| `auto-lint report <path> --format json` | Generate quality report (text/json/sarif/junit) |
| `auto-lint ci <path>`                   | CI mode with exit codes                         |

### Scans

| Command                           | Description                    |
| --------------------------------- | ------------------------------ |
| `auto-lint security <path>`     | Bandit vulnerability scan      |
| `auto-lint complexity <path>`   | Cyclomatic complexity analysis |
| `auto-lint duplicates <path>`   | Code duplication detection     |
| `auto-lint trends <path>`       | Quality trends over time       |
| `auto-lint dependencies <path>` | Dependency vulnerability scan  |

### Setup

| Command                        | Description                    |
| ------------------------------ | ------------------------------ |
| `auto-lint setup init`       | Auto-configure environment     |
| `auto-lint setup hermes`     | Auto-install into Hermes Agent |
| `auto-lint setup doctor`     | Diagnose issues                |
| `auto-lint setup mcp-config` | Print MCP config for clients   |

### Dev

| Command                               | Description                                 |
| ------------------------------------- | ------------------------------------------- |
| `auto-lint diff <path1> <path2>`    | Compare lint results between two versions   |
| `auto-lint suggest <path>`          | AI-powered fix suggestions (--ai flag)      |
| `auto-lint config show\|edit\|reset`  | View, edit, or reset configuration settings |
| `auto-lint export sarif\|junit\|json` | Export lint reports to file (-o output)     |
| `auto-lint import <config.json>`    | Import configurations from file             |
| `auto-lint ignore <rule>`           | Manage ignore rules (--remove to delete)    |
| `auto-lint init`                    | Initialize a new Auto-Linter configuration  |
| `auto-lint install-hook`            | Install git pre-commit hook                 |
| `auto-lint uninstall-hook`          | Remove git pre-commit hook                  |

### Maintenance

| Command                       | Description               |
| ----------------------------- | ------------------------- |
| `auto-lint cancel <job_id>` | Cancel a running lint job |
| `auto-lint stats <path>`    | Statistics dashboard      |
| `auto-lint clean`           | Cleanup cache             |
| `auto-lint update`          | Update adapters           |
| `auto-lint doctor`          | Diagnose issues           |
| `auto-lint version`         | Show version              |
| `auto-lint adapters`        | List enabled linters      |

### Other

| Command                             | Description                       |
| ----------------------------------- | --------------------------------- |
| `auto-lint watch <path>`          | Watch files, auto-lint on changes |
| `auto-lint batch <p1> <p2>`       | Check multiple paths              |
| `auto-lint plugins`               | List discovered plugins           |
| `auto-lint multi-project <paths>` | Lint multiple projects, aggregate |

## Transport

Connects to DesktopCommander for command execution. Auto-detected: socket -> http -> stdio.

```
DESKTOP_COMMANDER_URL              Mode             Requires
──────────────────────────────────────────────────────────────
/run/desktop-commander/socket      Unix Socket      DesktopCommander
http://localhost:24680/execute     HTTP             HTTP wrapper
auto (default)                     Auto-detect      tries socket -> http -> stdio
```

Default socket: `/run/desktop-commander/socket`

## Adapters

| Adapter    | Language   | Weight | Notes                |
| ---------- | ---------- | ------ | -------------------- |
| ruff       | Python     | 1.0    | Formatting + linting |
| mypy       | Python     | 1.0    | Type checking        |
| bandit     | Python     | 1.0    | Security scanning    |
| radon      | Python     | 1.0    | Complexity metrics   |
| eslint     | JS/TS      | 1.0    | Linting              |
| prettier   | JS/TS      | 0.5    | Formatting           |
| tsc        | TypeScript | 1.0    | Type checking        |
| governance | All        | 1.0    | Architecture rules   |

## Configuration

### .env (optional)

```bash
DESKTOP_COMMANDER_URL=/run/desktop-commander/socket
PHANTOM_ROOT=$HOME/
```

### auto_linter.config.yaml (optional)

```yaml
thresholds:
  score: 80.0
  complexity: 10
  max_file_lines: 500
```

---

## Governance Rules (Architecture Enforcement)

Governance rules are **configurable** - by default empty, but you can define rules for your architecture.

### AES Architecture (Auto-Linter's Own)

```yaml
# AES = Agent, Capabilities, Surfaces, Taxonomy, Infrastructure
layer_map:
  agent: agent
  capabilities: capabilities
  surfaces: surfaces
  taxonomy: taxonomy
  infrastructure: infrastructure

governance_rules:
  - from: surfaces
    to: infrastructure
    description: "Surface must not import Infrastructure directly"
  - from: capabilities
    to: infrastructure
    description: "Capabilities must not import Infrastructure (use Taxonomy)"
  - from: capabilities
    to: surfaces
    description: "Capabilities must not import Surface"
  - from: infrastructure
    to: surfaces
    description: "Infrastructure must not import Surface"
```

### Clean Architecture (Uncle Bob)

```yaml
layer_map:
  entities: entities
  usecases: usecases
  interfaces: interfaces
  frameworks: frameworks

governance_rules:
  - from: entities
    to: usecases
    description: "Entities should not know Use Cases"
  - from: usecases
    to: interfaces
    description: "Use Cases must not know Framework details"
```

### Hexagonal Architecture (Ports & Adapters)

```yaml
layer_map:
  domain: domain
  application: application
  ports: ports
  adapters: adapters

governance_rules:
  - from: domain
    to: application
    description: "Domain should not depend on Application"
  - from: domain
    to: adapters
    description: "Domain should not depend on Adapters"
  - from: adapters
    to: domain
    description: "Adapters must use Ports to access Domain"
```

### Onion Architecture

```yaml
layer_map:
  core: core
  application: application
  infrastructure: infrastructure

governance_rules:
  - from: core
    to: application
    description: "Core must not know Application layer"
  - from: core
    to: infrastructure
    description: "Core must not know Infrastructure"
```

### DDD (Domain-Driven Design)

```yaml
layer_map:
  domain: domain
  application: application
  infrastructure: infrastructure
  interfaces: interfaces

governance_rules:
  - from: domain
    to: infrastructure
    description: "Domain must not depend on Infrastructure"
  - from: domain
    to: application
    description: "Domain should be framework-agnostic"
```
