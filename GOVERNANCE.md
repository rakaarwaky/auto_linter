# Architectural Governance & Project Standards

This document outlines the governance model, contribution standards, and architectural invariants for the **Auto Linter** project. We adhere to the Agentic Engineering System (AES) principles, treating code as an economic asset where technical debt is minimized through empirical verification.

## 1. Project Governance Model

The Auto Linter project operates under a maintainer-led governance model. Decisions regarding architectural shifts, new language support, and core capability extensions are guided by the principles of **Methodological Skepticism**. All changes must be backed by empirical data (metrics, test coverage, static analysis).

## 2. Empirical Verification Standards

To prevent architectural drift and semantic entropy, every pull request or push to the main branch MUST satisfy the following criteria:

- **Logic Integrity**: A minimum of **95% Test Coverage** is required across all domains (`src/`). Untested code is considered a liability.
- **Surface & Format Integrity**: The project must maintain a **100.0 Governance Score**. This means zero stylistic warnings, zero unused imports, zero type errors, and zero unresolved static analysis issues across all supported tools (Ruff, MyPy, Prettier, ESLint, TSC).

## 3. Structural Invariants

When modifying or auditing this asset, the following structural invariants are actively enforced:

1. **Taxonomy (Explicit Definition)**: All domains exist precisely in one core entity (`src/`). Names must be explicit and avoid abbreviations (e.g., `governance.py`, not `gov.py`).
2. **Capability (Vertical Slicing)**: Features are organized by vertical slices around core concepts such as `adapters`, `actions`, and the underlying MCP `server`. Everything a feature needs lives in one cohesive location.
3. **Infrastructure (Replaceability)**: Third-party tools (e.g., Ruff, ESLint) are treated as replaceable adapters. The core logic must never be tightly coupled to a specific external tool's implementation details.
4. **Surface (Strict Boundaries)**: The sole ingestion surface is the FastMCP server implementation (`src/surfaces/mcp/server.py`). The boundary between internal domain logic and external exposure is absolute. Functionality must be reachable from a Surface.

## 4. Decision-Making Process

1. **Proposals**: Significant changes should be proposed via an Issue, detailing the "Why" and the empirical impact.
2. **Implementation**: Code changes must follow the structural invariants listed above. Max directory depth is 5 levels. One file, one concern.
3. **Review**: Maintainers will review the Code Coverage report and Linting/Governance score before approving. Subjective style debates are deferred to automated formatters.

By contributing to this repository, you agree to uphold these standards to ensure the continuous operational excellence of the Auto Linter infrastructure.
