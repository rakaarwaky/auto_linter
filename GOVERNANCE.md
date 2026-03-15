# Architectural Governance & Project Standards

This document outlines the governance model, contribution standards, architectural invariants, and community guidelines for the **Auto Linter** project. We adhere to the **Agentic Engineering System (AES)** principles: code is treated as an economic asset where technical debt must be eliminated through empirical verification.

---

## 1. Project Governance Model

The Auto Linter project operates under a strictly **Maintainer-Led Governance Model** focused on meritocracy and empirical data.
Decisions regarding architectural shifts, new language support, and core capability extensions are guided by the principles of **Methodological Skepticism**. 
All changes—regardless of the author—must be backed by empirical data, including metrics, 100% test coverage, and static analysis clearance.

### 1.1 Roles and Responsibilities
- **Users/Consumers**: Anyone utilizing the MCP server. Feedback is provided via GitHub Issues.
- **Contributors**: Individuals submitting Pull Requests (PRs). Must adhere strictly to the "Empirical Verification Standards."
- **Maintainers**: Core team members responsible for merge approvals, architectural enforcement, and release management.

## 2. Empirical Verification Standards

To prevent architectural drift and semantic entropy, every pull request or push to the `main` branch MUST satisfy the following criteria:

- **Logic Integrity (Coverage)**: A strict **100% Test Coverage** is required across all domains (`src/`). Untested code is considered a liability and will be rejected by CI.
- **Surface & Format Integrity**: The project must maintain a **100.0 Governance Score**. This translates to:
  - Zero stylistic warnings
  - Zero unused imports
  - Zero type errors
  - Zero unresolved static analysis issues across all supported tools (Ruff, MyPy, Prettier, ESLint, TSC).

## 3. Structural Invariants

When modifying or auditing this asset, the following structural invariants are actively enforced:

1. **Taxonomy (Explicit Definition)**: All domains exist precisely in one core entity (`src/`). Names must be explicit and avoid abbreviations (e.g., `governance.py`, never `gov.py`).
2. **Capability (Vertical Slicing)**: Features are organized by vertical slices around core concepts such as `adapters`, `actions`, and the underlying MCP `server`. Everything a feature needs lives in one cohesive location.
3. **Infrastructure (Replaceability)**: Third-party tools (e.g., Ruff, ESLint) are treated as replaceable adapters. Core business logic must never be tightly coupled to a specific external tool's implementation details.
4. **Surface (Strict Boundaries)**: The sole ingestion surface is the FastMCP server implementation (`src/surfaces/mcp/server.py`). The boundary between internal domain logic and external exposure is absolute.

## 4. Decision-Making & Contribution Process

We welcome contributions that align with our architectural vision. Please follow this lifecycle:

1. **Proposals & RFCs**: Significant changes must be proposed via a GitHub Issue detailing the "Why," the economic/architectural impact, and the proposed implementation methodology.
2. **Implementation**: Code changes must follow the structural invariants listed above. 
   - Maximum directory depth is 5 levels. 
   - Follow the "One file, one concern" principle.
3. **Review & Merge**: Maintainers will review the Code Coverage report and Linting/Governance score before approving. Subjective style debates are deferred to automated formatters. If the CI fails, the PR will not be reviewed.
4. **Release Management**: We follow Semantic Versioning (SemVer). The maintainers handle cutting releases and publishing changelogs based on merged PRs.

## 5. Security & Code of Conduct

- **Security Reporting**: If you discover a potential security vulnerability, do not open a public issue. Please report it privately to the repository maintainers.
- **Code of Conduct**: We expect professional, respectful communication in all issues, pull requests, and discussions. Ad hominem attacks, harassment, or completely unsubstantiated architectural claims will not be tolerated.

By contributing to this repository, you agree to uphold these standards to ensure the continuous operational excellence of the Auto Linter infrastructure.
