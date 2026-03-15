# Auto Linter (MCP Server)

[![Maintainability](https://img.shields.io/badge/Maintainability-A-green.svg)](https://github.com/rakaarwaky/auto_linter)
[![Coverage](https://img.shields.io/badge/Coverage-97%25-brightgreen.svg)](https://github.com/rakaarwaky/auto_linter)
[![Governance](https://img.shields.io/badge/Governance-100.0-blue.svg)](GOVERNANCE.md)

Auto Linter is a Model Context Protocol (MCP) Server that provides autonomous, multi-language linting, type-checking, and governance auditing for software projects. Designed to support robust engineering workflows, it enforces strict code quality and architectural standards.

## 🚀 Features

- **Multi-Language Support**: Seamlessly analyzes Python (Ruff, MyPy, Pyre) and JavaScript/TypeScript (ESLint, Prettier, TSC).
- **Autonomous Fixes**: Automatically applies safe fixes to resolve formatting and structural issues without manual intervention.
- **Strict Governance Check**: Enforces a 100.0 governance score to prevent architectural drift and ensure maximum maintainability.
- **Extensible Architecture**: Built on clean architecture principles, making it easy to add new linters or language adapters.

## 📦 Installation

To use this MCP server, ensure you have Python 3.10+ and the `uv` package manager installed.

```bash
# Clone the repository
git clone https://github.com/rakaarwaky/auto_linter.git
cd auto_linter

# Install dependencies using uv
uv sync
```

## 💻 Usage

### As an MCP Server

Auto Linter exposes two primary tools through the MCP interface:

1. `mcp_auto_linter_apply_safe_fixes`: Automatically applies safe fixes (e.g., Ruff fixes) to a specified file or directory.
2. `mcp_auto_linter_run_lint_check`: Runs a comprehensive analysis across all registered adapters and returns a structured governance report.

To run the server:
```bash
uv run fastmcp run src/surfaces/mcp/server.py
```

### For AI Agents (SKILL)

If you are an AI agent or assistant integrating this capability, please refer to [SKILL.md](SKILL.md) for standard operating procedures and usage constraints.

## 🏗️ Architecture

The project follows a strict vertical slice architecture (Clean Architecture):

- `src/core/`: Contains taxonomy (models, path utilities) and capabilities (actions, governance logic).
- `src/infrastructure/`: Contains language-specific adapters (Python, JavaScript) and semantic tracers.
- `src/surfaces/`: Contains the FastMCP server definition and tool exposures.
- `src/bootstrap/`: Contains dependency injection and container initialization.

## 🤝 Contributing & Governance

We adhere to a strict empirical verification model. All contributions must maintain **95%+ test coverage** and a **100.0 governance score**. 

Please see [GOVERNANCE.md](GOVERNANCE.md) for detailed rules on project governance and architectural standards.

## 📄 License

This project is licensed under the MIT License.
