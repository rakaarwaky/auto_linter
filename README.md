# Auto Linter (MCP Server)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Maintainability](https://img.shields.io/badge/Maintainability-A-green.svg)](https://github.com/rakaarwaky/auto_linter)
[![Test Coverage](https://img.shields.io/badge/Coverage-100%25-brightgreen.svg)](https://github.com/rakaarwaky/auto_linter)
[![Governance](https://img.shields.io/badge/Governance-Strict-blue.svg)](GOVERNANCE.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Auto Linter** is an advanced Model Context Protocol (MCP) Server that provides autonomous, multi-language linting, type-checking, and architectural governance auditing for software projects. Designed to support robust engineering workflows, it enforces strict code quality and structural invariants under the Agentic Engineering System (AES) principles.

---

## 📑 Table of Contents
- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
  - [As an MCP Server](#as-an-mcp-server)
  - [For AI Agents](#for-ai-agents)
- [Architecture](#%EF%B8%8F-architecture)
- [Contributing & Governance](#-contributing--governance)
- [License](#-license)

## 🚀 Features

- **Multi-Language Support**: Seamlessly analyzes Python (Ruff, MyPy, Pyre) and JavaScript/TypeScript (ESLint, Prettier, TSC).
- **Autonomous Fixes**: Automatically applies safe fixes to resolve formatting and structural issues without manual intervention.
- **Strict Governance Check**: Enforces a 100/100 governance score to prevent architectural drift and ensure maximum maintainability.
- **Agentic Extensibility**: Specifically designed for interaction with AI agents, offering atomic tools for code remediation.
- **Clean Architecture Principles**: Built on a solid foundation of Dependency Injection and vertical slicing, making it easy to add new linters or language adapters.

## 📦 Installation

To run the Auto Linter MCP server, you must have **Python 3.10+** and the [`uv`](https://github.com/astral-sh/uv) package manager installed on your system.

```bash
# 1. Clone the repository
git clone https://github.com/rakaarwaky/auto_linter.git
cd auto_linter

# 2. Install dependencies via uv
uv sync
```

## 💻 Usage

### As an MCP Server

Auto Linter exposes two primary tools through the MCP interface, enabling AI agents or IDEs to interact with the project:

1. `mcp_auto_linter_apply_safe_fixes`: Automatically applies safe fixes (e.g., Ruff fixes) to a specified file or directory.
2. `mcp_auto_linter_run_lint_check`: Runs a comprehensive analysis across all registered adapters and returns a structured governance report.

To start the server:

```bash
uv run fastmcp run src/surfaces/mcp/server.py
```

### For AI Agents

If you are an AI agent or assistant integrating this capability, you must read and adhere to the Standard Operating Procedures detailed in [SKILL.md](SKILL.md).

## 🏗️ Architecture

The project strictly follows a vertical slice architecture based on Clean Architecture principles:

- `src/core/`: Contains the fundamental taxonomy (models, path utilities) and core capabilities (actions, governance logic).
- `src/infrastructure/`: Contains language-specific adapters (Python, JavaScript) and semantic tracers that interface with external tools.
- `src/surfaces/`: Contains the FastMCP server definition, API boundaries, and tool exposures.
- `src/bootstrap/`: Contains dependency injection and container initialization.

## 🤝 Contributing & Governance

We welcome community contributions but maintain extremely strict quality standards. We adhere to an empirical verification model mapping directly to AES (Agentic Engineering System).

- **100% Test Coverage** is required.
- **100/100 Governance Score** must be maintained.
- Please read our comprehensive [GOVERNANCE.md](GOVERNANCE.md) before submitting a Pull Request.

## 📄 License

This project is open-sourced under the MIT License.
