---
name: auto_linter
description: Core Infrastructure for Autonomous Linting & Governance Auditing.
version: 1.0.0
architecture: Clean Architecture
verified: 95% Coverage, 100.0 Score
---

# Auto Linter Skill

This document provides the Standard Operating Procedure (SOP) for integrating and utilizing the Auto Linter MCP Server. It is designed for AI agents and automated systems (referred to as "The Builder") interacting with the codebase.

## Overview

The `auto_linter` is a mandatory piece of development infrastructure. It provides empirical verification for logic and formatting changes, enforcing strict code quality standards across Python and JavaScript ecosystems.

## Core Capabilities

1. **Multi-Engine Static Analysis**: Orchestrates concurrent analysis using industry-standard tools:
   - Python: Ruff, MyPy, Pyre
   - JavaScript/TypeScript: ESLint, Prettier, TSC
2. **Automated Governance**: Identifies architectural drift, complex files, and missing vertical integrations.
3. **Safe Auto-Fixing**: Automatically resolves common stylistic and syntactic errors.

## Standard Operating Procedure (SOP)

Agents MUST utilize the `auto_linter` MCP tools in the following sequence during the development lifecycle:

### Phase 1: Clean & Format (`apply_safe_fixes`)

- **When to use**: IMMEDIATELY following the creation or modification of any source code file.
- **Action**: Call `mcp_auto_linter_apply_safe_fixes` with the absolute path to the modified file or directory.
- **Purpose**: Automatically standardizes formatting, removes unused imports, and resolves basic stylistic errors before deeper semantic analysis occurs.

### Phase 2: Deep Audit (`run_lint_check`)

- **When to use**: After `apply_safe_fixes` has completed, or when initially auditing an existing asset prior to modification.
- **Action**: Call `mcp_auto_linter_run_lint_check` with the absolute path.
- **Purpose**: Executes deep semantic analysis, type-checking, and overall governance auditing.
- **Success Criteria**: The tool MUST return `is_passing: true` with a score of `100.0`.

### Phase 3: Resolution & Mitigation

If `run_lint_check` returns a score below `100.0` or `is_passing: false`:
1. **Identify**: Review the structured output to locate the specific file, line, and rule violation. Code with errors is considered a liability.
2. **Resolve**: Use appropriate code editing tools to manually correct the logic, type hints, or structural failure.
3. **Re-verify**: You MUST execute `run_lint_check` again after making corrections. Do not proceed to other tasks until the governance score is restored to 100.0.
