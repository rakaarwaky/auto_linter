# Architectural Governance & Asset Verification

> **"Code is an Asset. Architecture is Economics."**

## AES Identity

The `auto_linter` module operates as a **Tier 3 Semantic UID** (The Builder). Its primary responsibility is the enforcement of Code Governance and Quality Assurance within the Agentic Engineering System (AES) framework. It acts as the "Constitution"—defining the precise rules of engagement for how code is formatted and presented to the system.

## Verification Protocol

As a core piece of infrastructure that controls quality assurance, its own integrity is paramount. It adheres to **Methodological Skepticism** and strictly relies on empirical verification.

### Empirical Status (Verified: 2026)

This module has been subjected to the highest standards of the AES framework:

- **Logic Integrity:** `95% Test Coverage` across all domains (`src/`).
- **Surface & Format Integrity:** `100.0 Governance Score`, completely void of stylistic warnings, unused imports, type errors, or architectural drift across Ruff, Mypy, Pyre, and Prettier.

## Operating Rules (The Builder Handshake)

When modifying or auditing this asset, the following structural invariants are actively enforced:

1. **TAXONOMY:** All domains exist precisely in one core entity (`src/`). Names are explicitly defined without abbreviations (e.g., `governance.py`).
2. **CAPABILITY:** Vertical slicing is utilized around the concepts of `adapters`, `actions`, and the underlying MCP `server`.
3. **INFRASTRUCTURE:** Testing (`tests/`) mirrors the vertical architecture of the working source code exactly.
4. **SURFACE:** The sole ingestion surface is the FastMCP server implementation (`src/surfaces/mcp/server.py`). The boundary between internal and external use cases is absolute.

## Sub-Adapters

This module uses an extensible class interface to interact with third-party tools, ensuring tech is treated as a replaceable adapter:

- Python: `Ruff`, `Mypy`, `Pyre`
- JavaScript/TypeScript: `ESLint`, `Prettier`, `TSC`
