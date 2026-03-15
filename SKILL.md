---
name: auto_linter
description: Core AES Infrastructure for Autonomous Linting & Governance Auditing.
version: 1.0.0
architecture: Clean Architecture
verified: 100% Coverage, 100.0 Score
---

# Auto Linter Skill 🧹

> **"Code is an Asset. Architecture is Economics."**

This is an **Agentic Operating Manual**. As a Tier 3 Semantic UID (The Builder), you MUST follow these protocols when modifying or creating code.

The `auto_linter` is a mandatory piece of your development infrastructure. It provides empirical verification for all logic changes, enforcing the strict formatting and structural rules of the AES framework.

## Empirical Status

The infrastructure you are using is completely verified:

- **100% Test Coverage**
- **100.0 Governance Score** across all tools (Ruff, MyPy, Pyre, ESLint, Prettier, TSC).

## Core Capabilities

1.  **Multi-Engine Analysis**: Simultaneously orchestrates Python (Ruff, MyPy, Pyre) and JavaScript/TypeScript (ESLint, Prettier, TSC) static analysis.
2.  **AES Governance Enforcement**: Identifies architectural drift, missing vertical slices, and overly complex files.
3.  **Self-Healing**: Automatically applies safe fixes to restore asset integrity.

## Agent Standard Operating Procedure (SOP)

You are equipped with two specialized tools from the `auto_linter` MCP server. You MUST use them in the following sequence:

### 1. `apply_safe_fixes`

- **When to use:** IMMEDIATELY after creating or modifying any file.
- **Purpose:** Automatically cleans up formatting, unused imports, and basic stylistic errors before you begin deeper analysis.
- **Action:** Call `mcp_auto_linter_apply_safe_fixes` with the absolute path to the file or directory.

### 2. `run_lint_check`

- **When to use:** After `apply_safe_fixes`, or when auditing an existing asset.
- **Purpose:** To perform a deep semantic analysis, type checking (MyPy/Pyre/TSC), and Governance auditing.
- **Action:** Call `mcp_auto_linter_run_lint_check` with the absolute path.
- **Condition for Success:** You MUST achieve a `100.0` score with `is_passing: true`. If the score is lower, you must manually resolve the reported errors (e.g., adding type hints, fixing undefined variables) and re-run the check until the asset passes.

## Failure Mitigation

If `run_lint_check` returns errors:

1. Do NOT ignore them. Code with errors is considered "Dead Stock" in the AES economic model.
2. Analyze the specific file, line, and code provided in the output.
3. Use your code editing tools to correct the logic or taxonomy failure.
4. Execute `run_lint_check` again to empirically verify the fix.

