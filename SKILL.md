---
name: auto-linter
description: Core Infrastructure for Autonomous Linting & Governance Auditing.
version: 1.0.0
standard: AES-2026-Skill
verified: 100% Coverage, 100.0 Score
---

# Auto Linter Skill 🛡️

This skill equips you with mandatory development infrastructure for empirical logic verification and automated governance. Use it to eliminate architectural drift and maintain a 100.0 quality score.

## 🧭 Agentic Directives

### 1. The 100.0 Score Gate
Any code missing a perfect governance score is considered a "Liability." You MUST achieve `is_passing: true` and a `score: 100.0` before declaring any task complete.
- **Tool**: Use `run_lint_check` to audit your assets.
- **Action**: Failure to meet this gate requires immediate remediation.

### 2. Governance-First Workflow
Infrastructure must precede execution.
1. **Format**: Apply `apply_safe_fixes` immediately after editing.
2. **Review**: Run `run_lint_check` to detect semantic or type violations.
3. **Iterate**: Do not move to functional testing until the surface is verified.

### 3. Inventory Control
Minimize "Dead Stock."
- Use the linter to identify unreachable code, unused imports, and redundant logic.
- Treat every line of code as a cost center that must be justified by reaching a Surface.

## 🛠 MCP Tools (9 tools total)

### Core Governance Tools (7 tools)

#### `run_lint_check(path: str)`
Run comprehensive linting analysis across all adapters. Orchestrates Ruff, MyPy, Bandit, Radon and more in one pass.

**Parameters**:
- `path` (str): Absolute path to file or directory for scanning

**Returns**: JSON string with violations per adapter + governance score object  
```json
{
  "ruff": [], // empty = no formatting issues
  "mypy": [{"file": "...", "line": 42, ...}], 
  "bandit": [], // security scan results
  "score": 95.5,
  "is_passing": true,
  "governance": {"threshold_met": true}
}
```

**When to use**: After every code change, before commits  
---

#### `apply_safe_fixes(path: str)`
Apply automatic safe fixes (Ruff for Python, ESLint/Prettier for JS/TS). Never makes breaking changes.

**Parameters**:
- `path` (str): Path to file or directory that needs fixing automatically!

**Returns**: JSON string with fix summary showing what was applied  
```json
{
  "fixes_applied": {
    "/path/to/file.py": ["Unused import removed", "Formatted code"],
    "./src/other.js": ["Prettier formatting"]
  },
  "total_fixes": 5,
  "errors_encountered": [] // empty means all fixes succeeded! ✅
}
```

**When to use**: Immediately after editing files before running full check  
---

#### `lint_security(path: str)`
Security vulnerability scan using Bandit. Detects SQL injection risks, XSS vulnerabilities, hardcoded secrets and more.

**Parameters**:
- `path` (str): Path to project directory for security scanning

**Returns**: JSON array of security violations with severity levels  
```json
[
  {
    "file": "/src/auth.py", 
    "line": 142, 
    "code": "B603", // Bandit error code
    "message": "SQL injection vulnerability detected!",
    "severity": "HIGH"
  }
]
```

**When to use**: Before release deployment or after adding new dependencies  
---

#### `lint_complexity(path: str)`
Code complexity analysis using Radon. Identifies functions exceeding cyclomatic complexity thresholds that need refactoring!

**Parameters**:
- `path` (str): Path to project directory for complexity scanning

**Returns**: JSON array of high-complexity function locations  
```json
[
  {
    "file": "/src/complex_logic.py", 
    "function": "process_data()",
    "line": 89,
    "score": 25 // Cyclomatic complexity score (threshold is typically ~10)
  }
]
```

**When to use**: During code review sessions or refactoring sprints  
---

#### `lint_dependencies(path: str)`
Dependency vulnerability scan using pip-audit. Checks requirements.txt and package.json for known CVEs!

**Parameters**:
- `path` (str): Project root directory containing dependency files

**Returns**: JSON array of vulnerable dependencies with patch versions recommended  
```json
[
  {
    "package": "requests", 
    "version": "2.19.0", // Vulnerable version found! ❌
    "cve_id": "CVE-2023-XXXXX",
    "advisory": "Known vulnerability in this package version"
  }
]
```

**When to use**: Weekly security scans or after updating dependencies  
---

#### `lint_duplicates(path: str)`
Duplicate code detection across the project. Finds copy-pasted logic and oversized files that violate single-responsibility principle!

**Parameters**:
- `path` (str): Path to scan for duplication patterns

**Returns**: JSON array of duplicate blocks with file locations  
```json
[
  {
    "file": "/src/utils.py", 
    "line_range": [45, 78], // Lines containing duplicated code! ⚠️
    "similarity_score": 0.92, // Very similar to another block elsewhere
    "duplicate_of": "/lib/legacy_utils.py:12-34"
  }
]
```

**When to use**: During refactoring sessions or before major code merges  
---

#### `lint_trends(path: str)`
Quality trends over time analysis. Detects regressions in governance score between check runs!

**Parameters**:
- `path` (str): Project directory for trend comparison against history  

**Returns**: JSON array of quality trend warnings if any regression detected  
```json
[
  {
    "metric": "governance_score", 
    "current_value": 85.0, // Dropped from previous run! ❌
    "previous_value": 92.3,
    "trend_direction": "DECLINING"
  }
]
```

**When to use**: Sprint retrospectives or before release candidate builds  
---

### Hybrid Architecture Tools (2 tools)

These enable **unlimited CLI command discovery and execution** without hitting MCP tool limits! 🚀

#### `list_commands(domain: str | None = None)`
List all available CLI commands with their descriptions. Enables agents to discover capabilities dynamically!

**Parameters**:
- Optional domain filter string (e.g., `"lint"`) - if provided, returns only matching sub-actions for that category

**Returns**: JSON object mapping command names → description + example_usage  
```json
{
  "check": {
    "description": "Run full governance analysis on path/file", 
    "example_usage": "auto-lint check /path/to/src/"
  },
  "fix": {
    "description": "Apply safe fixes automatically (Ruff, ESLint, Prettier)", 
    "example_usage": "auto-linter fix ./src/ --verbose"
  }
}

// With domain filter: {"lint": ["check", "scan", "fix", ...]}
```

**When to use**: When discovering what CLI actions are available before execution!  
---

#### `execute_command(action: str, args: dict | None = None)`
Execute ANY CLI command from the Auto-Linter catalog. Core of hybrid architecture pattern - enables unlimited scalability without tool limits! 🎯

**Parameters**:
- `action` (str): Command name from available commands list (e.g., `"check"`, `"fix"`)  
- Optional args dict with key-value pairs for optional command arguments: `{path: "./src/", format: "json", exit_zero: true}`

**Returns**: JSON object containing full subprocess output + return code!
```json
{
  "command": "auto-lint check ./src/ --format json", // Full CLI command executed!
  "stdout": "{\"score\":95.0,\"is_passing\":true,...}", // Command's stdout captured here! ✅
  "stderr": "", // Any stderr output (empty = success!) 
  "returncode": 0, // Exit code: 0=success, non-zero=failure/issue found ❌
}

// Error case example:
{
  "error": "Invalid action 'foobar'. Valid actions are: check, fix...",
  "valid_actions_count": 16,
  "suggestion": "Use one of the listed valid actions"
}
```

**When to use**: Execute any CLI command dynamically via MCP without hardcoding tool schemas!  
---

## 💻 CLI Commands (15+ commands)

### Core Commands

#### `auto-lint check <path>`
Run all linters and check governance score.

```bash
# Basic check
auto-lint check src/

# JSON output
auto-lint check src/ --format json
```

**Returns**: Score + violations per adapter

**When to use**: After every code change

---

#### `auto-lint scan <path>`
Full deep scan (alias for check).

```bash
auto-lint scan src/
```

---

#### `auto-lint fix <path>`
Apply safe fixes automatically.

```bash
auto-lint fix src/
```

**Fixes**:
- Unused imports (Ruff)
- Format issues (Prettier)
- Style violations (ESLint)

**When to use**: Immediately after editing

---

#### `auto-lint report <path>`
Generate detailed quality report.

```bash
# Text report
auto-lint report src/

# JSON for CI
auto-lint report src/ --format json

# SARIF for GitHub
auto-lint report src/ --format sarif

# JUnit for Jenkins
auto-lint report src/ --format junit
```

---

### Specialized Scans

#### `auto-lint security <path>`
Security vulnerability scan (Bandit).

```bash
auto-lint security src/
```

**Detects**: SQL injection, XSS, hardcoded secrets, etc.

**When to use**: Before release

---

#### `auto-lint complexity <path>`
Analyze code complexity.

```bash
auto-lint complexity src/
```

**Returns**: Functions exceeding complexity threshold

**When to use**: During refactoring

---

#### `auto-lint duplicates <path>`
Find duplicate code blocks.

```bash
auto-lint duplicates src/
```

---

#### `auto-lint trends <path>`
Show quality trends over time.

```bash
auto-lint trends .
```

**Returns**: Week-over-week scores

---

### CI/CD Commands

#### `auto-lint ci <path>`
CI/CD mode: fails if governance < 100.

```bash
# In CI pipeline
auto-lint ci src/ --exit-zero

# Exit code 1 if score < 100
auto-lint ci src/
```

**When to use**: Pre-merge gates

---

#### `auto-lint batch <paths...>`
Run on multiple paths.

```bash
auto-lint batch src/ tests/ scripts/
```

**Returns**: Pass/fail per path

---

### Setup Commands

#### `auto-lint init <path>`
Initialize configuration.

```bash
auto-lint init .
```

**Creates**: `.auto_linter.json`

---

#### `auto-lint install-hook`
Install git pre-commit hook.

```bash
auto-lint install-hook
```

**When to use**: Project setup

---

#### `auto-lint uninstall-hook`
Remove git pre-commit hook.

```bash
auto-lint uninstall-hook
```

---

#### `auto-lint version`
Show version information.

```bash
auto-lint version
```

---

#### `auto-lint adapters`
List available adapters.

```bash
auto-lint adapters
```

---

#### `auto-lint watch <path>`
Watch mode: auto-lint on file changes.

```bash
auto-lint watch src/
```

**When to use**: During development

---

## 🔄 Common Workflows

### Pre-Commit Quality Gate
```bash
# 1. Apply safe fixes
auto-lint fix src/

# 2. Run full check
auto-lint check src/

# 3. If governance < 100, fix violations
# 4. Re-check
auto-lint check src/
```

### CI/CD Pipeline
```yaml
# GitHub Actions example
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install auto-linter
      - run: auto-lint ci src/ --format sarif --output report.sarif
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: report.sarif
```

### Security Audit
```bash
# 1. Security scan
auto-lint security src/

# 2. Dependency scan
auto-lint dependencies .

# 3. Fix high-severity issues
# 4. Re-scan
auto-lint security src/
```

### Complexity Refactoring
```bash
# 1. Find complex functions
auto-lint complexity src/

# 2. Refactor listed functions

# 3. Verify improvement
auto-lint complexity src/
```

### Watch Mode Development
```bash
# Terminal 1: Start watch mode
auto-lint watch src/

# Terminal 2: Edit code
# Auto-linter runs automatically on save
```

## 📐 Governance Standards (AES-2026)

Ensure all implementations adhere to:
- **Max Depth 5**: Directory nesting ≤ 5 levels
- **Vertical Slicing**: Features cohesive within single slice
- **Explicit Frontiers**: Every file has clear Ingress/Egress

## ⚠️ Adapter Limitations

| Adapter | Limitations |
|---------|-------------|
| Ruff | Python only, safe fixes only |
| MyPy | Type hints required |
| ESLint | JS/TS only, needs config |
| Bandit | Python security only |
| Radon | Complexity metrics only |

## 🎯 Hybrid Architecture Pattern

This skill implements the **MCP+CLI+SKILL** hybrid pattern:

```
AI Agent
  ↓
5 MCP Tools (execute_command, list_commands, etc.)
  ↓
15+ CLI Commands (check, fix, report, etc.)
  ↓
SKILL.md Context (this file)
```

**Benefits**:
- ✅ Unlimited capabilities (not limited by MCP tool count)
- ✅ 84% token savings vs pure MCP
- ✅ Humans can use CLI directly
- ✅ AI agents use MCP tools

**Discovery**:
1. Read this SKILL.md (system context)
2. Call `list_commands()` for catalog
3. Use `execute_command(action, args)` for any command

---

> [!IMPORTANT]
> A score of 100.0 is mandatory. If you cannot resolve violations, switch to `PLANNING` mode and consult the Human Architect.

> [!NOTE]
> For production use, integrate with CI/CD using `auto-lint ci` with appropriate exit codes.
