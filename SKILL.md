---
version: 1.6.2
---
# Auto Linter Skill

> **GUIDE FOR AI AGENTS.**
> Humans: Use the `auto-lint` CLI directly in the terminal.

MCP Server for autonomous multi-language linting and architectural governance audits.

## Key Features
- **Multi-Linter**: Runs Ruff, MyPy, Bandit, Radon, pip-audit, ESLint, Prettier, and TSC in a single command.
- **Governance Audit**: Enforces architectural rules (e.g., "Surfaces are prohibited from importing Infrastructure").
- **Auto-Fix**: Automatically fixes code style issues (linting) without intervention.
- **Reporting**: Generates quality scores (0-100) and reports in JSON/SARIF/JUnit formats.
- **Hot Reload**: Supports live server code updates during development.

## Agent Workflow (Recommended)
1. `list_commands()` — Discover available commands.
2. `execute_command("check", {"path": "src/"})` — Run a quality audit.
3. `execute_command("fix", {"path": "src/"})` — Fix issues automatically.
4. `execute_command("report", {"path": "src/", "output-format": "json"})` — Retrieve detailed data.

## MCP Tools (5 tools)

### `execute_command(action, args)`
Execute any CLI command. This is the primary tool.
Example actions: check, fix, report, security, complexity, dependencies, setup, doctor.

### `list_commands(domain)`
Lists all available CLI commands along with examples.

### `read_skill_context(section)`
Read this SKILL.md documentation by section or in its entirety.

### `check_status(job_id)`
Check the status of long-running linting jobs.

### `health_check()`
Check system health: adapters, transport, and DesktopCommander connection.

## CLI Command List (auto-lint)

### Core
- `auto-lint check <path>`: Run all linters and calculate score.
- `auto-lint scan <path>`: Alias for check (CI-friendly).
- `auto-lint fix <path>`: Apply safe automatic fixes.
- `auto-lint report <path> --output-format json`: Generate detailed quality reports.
- `auto-lint ci <path>`: CI mode (exit code 1 if score < threshold).

### Scans
- `auto-lint security <path>`: Scan for vulnerabilities using Bandit.
- `auto-lint complexity <path>`: Cyclomatic complexity analysis (Radon).
- `auto-lint duplicates <path>`: Detect code duplication or SRP violations.
- `auto-lint trends <path>`: Monitor quality trends over time.
- `auto-lint dependencies <path>`: Scan for library vulnerabilities (pip-audit).

### Setup & Maintenance
- `auto-lint setup doctor`: Diagnose environment health and linter binaries.
- `auto-lint setup init`: Automatic environment configuration.
- `auto-lint setup hermes`: Auto-install into Hermes Agent.
- `auto-lint setup mcp-config`: Print MCP configuration for clients.
- `auto-lint adapters`: List all active linters.
- `auto-lint version`: Show current version (1.6.2).
- `auto-lint config show`: View active configuration (YAML).
- `auto-lint cancel <job_id>`: Cancel a running lint job.

### Dev
- `auto-lint watch <path>`: Monitor files and run lint automatically on changes.
- `auto-lint suggest <path>`: Provide improvement suggestions (can use --ai).
- `auto-lint install-hook`: Install git pre-commit hook.
- `auto-lint uninstall-hook`: Remove git pre-commit hook.

## Architectural Rules (Governance)
Architectural audits are configured in `auto_linter.config.yaml` through `layer_map` and `governance_rules`.
Each violation will drastically reduce the quality score (Critical = -50 points).
