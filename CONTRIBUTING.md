# Contributing to Auto Linter

> **Join 5+ Contributors Building the Future of Automated Code Quality**

Thank you for your interest. This guide covers everything you need
to start contributing effectively.

## Why Contribute

| Perks                           | Benefit                                     |
| ------------------------------- | ------------------------------------------- |
| **Real-world impact**     | Your code helps 500+ teams ship better code |
| **Portfolio builder**     | Showcase pytest, async, MCP skills          |
| **Open source cred**      | Stand out in job applications               |
| **Community recognition** | GitHub contributors, discord shoutouts      |
| **Learning opportunity**  | Study well-architected 5-domain codebase    |

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Architecture](#architecture)
- [How to Add an Adapter](#how-to-add-an-adapter)
- [How to Add a CLI Command](#how-to-add-a-cli-command)
- [How to Add an MCP Tool](#how-to-add-an-mcp-tool)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)

---

## Prerequisites

- Python >= 3.12
- uv (recommended) or pip
- Git
- Familiarity with:
  - Python asyncio
  - Click (CLI framework)
  - mcp (MCP protocol library)
  - pytest

---

## Setup

```bash
# Clone
git clone https://github.com/rakaarwaky/auto_linter.git
cd auto_linter

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"

# Verify installation
python3 -m pytest tests/ -q
# Expected: 1500+ passed

# Check version
python3 -m surfaces.cli_main_entry version
```

---

## Architecture

### 5-Domain Model

```
src/
  agent/              Wiring layer -- DI container, lifecycle
  capabilities/       Thinking layer -- analysis logic, use cases
  infrastructure/     Toolbox layer -- linter adapters, clients
  surfaces/           Interface layer -- CLI, MCP tools
  taxonomy/           Language layer -- models, interfaces
```

### Dependency Rules

Imports must follow AES layer rules:

```
surfaces      --> capabilities       OK
surfaces      --> infrastructure     NO
capabilities  --> infrastructure     NO (use taxonomy interfaces)
capabilities  --> surfaces           NO
infrastructure --> taxonomy          OK
agent         --> everything         OK (wiring layer)
```

The `GovernanceAdapter` enforces these rules automatically.
Run `auto-lint check src/` to verify no violations.

### Key Interfaces

All adapters implement `ILinterAdapter` (defined in `taxonomy/`).
Use cases orchestrate adapters and semantic tracers.
See existing adapters in `infrastructure/` and `capabilities/` for the current API.

### Data Flow

```
User/Agent
    |
    v
Surface (CLI or MCP)
    |
    v
Container (DI) --> UseCase (capabilities/)
    |                  |
    v                  v
Adapter (infrastructure/) --> External tool (subprocess)
    |
    v
LintResult (taxonomy/)
    |
    v
GovernanceReport --> Formatter (SARIF/JUnit/JSON/Text)
```

---

## How to Add an Adapter

### 1. Create the adapter file

File: `src/infrastructure/<language>_<tool>_adapter.py`

Implement `ILinterAdapter` from `taxonomy/`. See existing adapters for the current API.
The `source` field in `LintResult` should use the adapter's name.

```python
"""Adapter for <ToolName>."""
from taxonomy import ILinterAdapter, LintResult

class MyToolAdapter(ILinterAdapter):
    def name(self) -> str:
        return "my-tool"

    def scan(self, path):
        # Run external tool, parse into LintResult objects
        ...

    def apply_fix(self, path) -> bool:
        # Return True if fixes were applied
        ...
```

### 2. Register in DI container

File: `src/agent/dependency_injection_container.py`

Add your adapter to the `self.adapters` list:

```python
from infrastructure.my_tool_adapter import MyToolAdapter

self.adapters: List[ILinterAdapter] = [
    ...existing adapters...,
    MyToolAdapter(bin_path=vbin),
]
```

### 3. Add tests

File: `tests/infrastructure/test_my_tool_adapter.py`

```python
from unittest.mock import patch, MagicMock
from infrastructure.my_tool_adapter import MyToolAdapter

def test_my_tool_name():
    assert MyToolAdapter().name() == "my-tool"

@patch("subprocess.run")
def test_my_tool_scan(mock_run):
    mock_run.return_value = MagicMock(stdout="...", stderr="", returncode=0)
    results = MyToolAdapter().scan("test.py")
    assert isinstance(results, list)
```

### 4. Run tests

```bash
python3 -m pytest tests/infrastructure/test_my_tool_adapter.py -v
python3 -m pytest tests/ --cov=src --cov-report=term-missing
```

---

## How to Add a CLI Command

### 1. Choose the right module

| Module                          | Purpose                                                                           |
| ------------------------------- | --------------------------------------------------------------------------------- |
| `cli_core_commands.py`        | check, scan, fix, report, version, adapters, security, cancel                     |
| `cli_analysis_commands.py`    | complexity, duplicates, trends, dependencies, ci, batch                           |
| `cli_dev_commands.py`         | diff, suggest, ignore, config, export, import, init, install-hook, uninstall-hook |
| `cli_maintenance_commands.py` | stats, clean, update, doctor, cancel                                              |
| `cli_setup_commands.py`       | setup init, setup hermes, setup doctor, setup mcp-config                          |
| `cli_watch_commands.py`       | watch                                                                             |

Each file should stay under 300 lines. If it would exceed that,
create a new `cli_<domain>_commands.py` file.

### 2. Add the command

```python
# In the appropriate cli_*_commands.py file

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--threshold', default=15, type=int)
def my_command(path, threshold):
    """Short description shown in --help."""
    container = get_container()
    abs_path = os.path.abspath(path)

    async def _run():
        click.echo(f"Running on {abs_path}...")
        # Use container.use_cases or adapters
        ...

    asyncio.run(_run())
```

### 3. Register in catalog

File: `src/surfaces/mcp_command_catalog.py`

Add to `_COMMAND_CATALOG`:

```python
"my-command": {
    "description": "What it does",
    "example": "auto-lint my-command /path",
},
```

### 4. Add tests

Test via CliRunner (integration) or test the underlying
use case directly (unit):

```python
from click.testing import CliRunner
from surfaces.cli_core_commands import cli

def test_my_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['my-command', 'test.py'])
    assert result.exit_code == 0
```

---

## How to Add an MCP Tool

### 1. Add to registry

File: `src/surfaces/mcp_tools_registry.py`

```python
import json
from mcp import types

def tool_my_tool():
    return types.Tool(
        name="my_tool",
        description="Tool description shown to AI agents.",
        inputSchema={
            "type": "object",
            "properties": {"param": {"type": "string"}},
            "required": ["param"],
        },
    ), _handle_my_tool

async def _handle_my_tool(arguments: dict) -> str:
    # Implementation
    return json.dumps({"result": "..."})

# Add to ALL_TOOLS list:
ALL_TOOLS = [
    ...existing tools...,
    tool_my_tool,
]
```

### 2. Add tests

```python
import json
import pytest

@pytest.mark.asyncio
async def test_my_tool():
    from surfaces.mcp_tools_registry import tool_my_tool
    tool_def, handler = tool_my_tool()
    assert tool_def.name == "my_tool"
    result = await handler({"param": "value"})
    assert "result" in json.loads(result)
```

---

## Testing

### Run all tests

```bash
python3 -m pytest tests/ -v --tb=short
```

### Run with coverage

```bash
python3 -m pytest tests/ --cov=src --cov-report=term-missing
```

### Run specific test file

```bash
python3 -m pytest tests/infrastructure/test_adapters_python.py -v
```

### Test structure

```
tests/
  agent/                  DI container tests
  capabilities/           Use case and formatter tests
  infrastructure/         Adapter tests (mock subprocess)
  surfaces/               CLI and MCP tool tests
  taxonomy/               Model and utility tests
  conftest.py             Shared fixtures
  test_protocols.py       DesktopCommander protocol tests
```

### Rules

- Every new function needs at least one test
- Mock external tools (subprocess, filesystem, network)
- Test both success and failure paths
- Use `@pytest.mark.asyncio` for async tests

---

## Code Style

### Formatting

```bash
# Auto-format
auto-lint fix src/

# Check only
auto-lint check src/
```

### Conventions

- Python 3.12+ features encouraged (type hints, match/case)
- Async where possible (subprocess calls are sync, wrap in async)
- No bare `except:` — always catch specific exceptions
- Log errors, don't silently swallow them
- Keep files under 300 lines
- One class per file preferred, max 2 related classes
- Module docstrings: 1 line goal only

### Naming

- Adapters: `<Tool>Adapter` (e.g., `RuffAdapter`)
- Use cases: `<Action>UseCase` (e.g., `RunAnalysisUseCase`)
- CLI modules: `cli_<domain>_commands.py`
- MCP modules: `mcp_<function>.py`
- Test files: `test_<module>.py`

---

## Pull Request Process

### Before Submitting

1. **Run tests**: `python3 -m pytest tests/ -q`
   All tests must pass. No skipped tests without justification.
2. **Run linter**: `auto-lint check src/`
   Fix all violations. Governance score must be high.
3. **Check coverage**: `python3 -m pytest tests/ --cov=src`
   New code should have tests. Don't decrease total coverage.
4. **Update docs**:

   - PRD.md if you added features
   - SKILL.md if you changed MCP tools or CLI commands
   - README.md if the user-facing interface changed

### PR Description Template

```
## What
Brief description of what this PR does.

## Why
Why is this change needed?

## How
How does it work? Any design decisions?

## Testing
How was it tested? What test cases were added?

## Checklist
- [ ] Tests passing (1500+)
- [ ] No governance violations
- [ ] Coverage not decreased
- [ ] Docs updated if needed
```

### Review Criteria

- Code follows architecture rules (no cross-layer violations)
- Tests cover both happy path and error cases
- No hardcoded paths or environment assumptions
- Subprocess calls use absolute paths to executables
- Error messages are actionable (tell the user what to do)

---

## Questions?

Open an issue on GitHub or contact the maintainer.
