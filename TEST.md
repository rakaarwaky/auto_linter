# Local AI Prompt: End-to-End Auto Linter CLI Testing

**Instructions:** You are an AI capable of running terminal commands. Perform an end-to-end test of **every** CLI command listed below sequentially within the `auto_linter` project root directory. For each command, record:

- The command executed
- **Exit code** – must be 0 unless specified otherwise
- **Success indicator** (specific string that must appear in the output, or a file successfully created)
- If a command fails, stop the testing and report the cause.

### Initial Setup
```bash
# Ensure you are in the auto_linter project root
cd /home/raka/mcp-servers/auto_linter

# Create and activate a virtual environment (if not already done)
python3.12 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install the project in development mode
pip install -e ".[dev]"

# Verify CLI availability
auto-lint version
```
**Success Indicator:** Output displays version `1.5.0` (or the latest version). Exit code 0.

### Prepare Test Project
```bash
mkdir -p test_project/src
cat > test_project/src/bad.py << 'EOF'
import os
import sys

def MyFunction():
    x = 1
    return x
EOF

cat > test_project/src/style.py << 'EOF'
var="hello"
print(var)
EOF

cat > test_project/src/security.py << 'EOF'
import subprocess
subprocess.call("ls", shell=True)
EOF

# Create a file >500 lines for duplicate testing
for i in {1..600}; do echo "line $i" >> test_project/src/large.py; done

cat > test_project/src/test.js << 'EOF'
function myFunc() {
    let x = 1;
    return x;
}
EOF
```

---

## CLI Command Testing (Core)

### 1. `auto-lint check test_project/src/`
**Success Indicator:** Exit code 0. Output contains `Score: .../100.0` and a list of issues (e.g., `ruff`, `mypy`, `bandit`, `governance`). Score is not 100.

### 2. `auto-lint scan test_project/src/`
**Success Indicator:** Output is the same as `check`. Exit code 0.

### 3. `auto-lint fix test_project/src/`
**Success Indicator:** Exit code 0. Output contains `Applied automatic fixes` for supported adapters (ruff, prettier, eslint). File `test_project/src/style.py` is modified (spaces around `=`).

### 4. `auto-lint report test_project/src/ --output-format text`
**Success Indicator:** Exit code 0. Text output listing every issue.

### 5. `auto-lint report test_project/src/ --output-format json`
**Success Indicator:** Exit code 0. Output is valid JSON containing `score`, `is_passing`, and adapter names fields.

### 6. `auto-lint report test_project/src/ --output-format sarif`
**Success Indicator:** Exit code 0. JSON output with SARIF 2.1.0 `$schema`.

### 7. `auto-lint report test_project/src/ --output-format junit`
**Success Indicator:** Exit code 0. XML output with `<testsuites>` root.

### 8. `auto-lint ci test_project/src/`
**Success Indicator:** Exit code 1 (because score < threshold, e.g., 80). Output contains `passing=False`.

---

## Analysis Command Testing (Scans)

### 9. `auto-lint security test_project/src/`
**Success Indicator:** Exit code 0. Output contains `Found 1 vulnerabilities` (Bandit detects `subprocess.call` with shell=True).

### 10. `auto-lint complexity test_project/src/`
**Success Indicator:** Exit code 0. Output contains `high complexity` or the function name `MyFunction`.

### 11. `auto-lint duplicates test_project/src/`
**Success Indicator:** Exit code 0. Output contains `exceeds 500 lines` for `large.py`.

### 12. `auto-lint trends test_project/src/`
**Success Indicator:** Exit code 0. Output contains `STABLE or IMPROVING` (due to new history) or another message without error.

### 13. `auto-lint dependencies test_project/src/`
**Success Indicator:** Exit code 0. Output contains `No dependency vulnerabilities found` (as there is no requirements.txt).

---

## Setup & Maintenance Command Testing

### 14. `auto-lint setup init`
**Success Indicator:** Exit code 0. `.env` file created in the current directory. Output contains `Setup complete!`.

### 15. `auto-lint setup doctor`
**Success Indicator:** Exit code 0. Output contains `All checks passed!` or a list of issues (non-fatal). Ensure no traceback occurs.

### 16. `auto-lint setup mcp-config --client all`
**Success Indicator:** Exit code 0. Output prints MCP configuration for Claude, Hermes, and VS Code in JSON format.

### 17. `auto-lint adapters`
**Success Indicator:** Exit code 0. Output lists at least `ruff`, `mypy`, `bandit`, `radon`, `governance`, `prettier`, `tsc`, `eslint`.

### 18. `auto-lint version`
**Success Indicator:** Exit code 0. Output `Auto-Linter v1.5.0`.

### 19. `auto-lint config show`
**Success Indicator:** Exit code 0. Output displays YAML configuration (thresholds, adapters, etc.).

---

## Development Command Testing (Dev)

### 20. `auto-lint watch test_project/src/`
Run this command, wait 3 seconds, then press **Ctrl+C** to stop.
**Success Indicator:** While running, output `Watching ... for changes...`. No errors. After Ctrl+C, the program stops gracefully.

### 21. `auto-lint suggest test_project/src/bad.py`
**Success Indicator:** Exit code 0. Output contains `Governance score is ...` and a suggestion to run `auto-lint fix`.

### 22. `auto-lint install-hook`
**Success Indicator:** Exit code 0. Output `Pre-commit hook installed successfully.` (Ignore if not a git repo, it might say `not a git repository` – this is also considered success).

### 23. `auto-lint uninstall-hook`
**Success Indicator:** Exit code 0. Output `Pre-commit hook removed successfully.` (or `not a git repository`).

---

## Additional Command Testing (From SKILL.md)

### 24. `auto-lint git-diff`
**Success Indicator:** Exit code 0. Output shows a list of changed files (or `No changed files detected` if no git changes). No errors.

### 25. `auto-lint diff test_project/src/bad.py test_project/src/style.py`
**Success Indicator:** Exit code 0. Output compares scores between two files (e.g., `Difference: +... IMPROVED`).

### 26. `auto-lint ignore E501`
**Success Indicator:** Exit code 0. Output `Added 'E501' to ignore list`. (Modifies `auto_linter.config.yaml` if it exists.)

### 27. `auto-lint export json -o report.json`
**Success Indicator:** Exit code 0. `report.json` file created and contains the report JSON.

### 28. `auto-lint clean`
**Success Indicator:** Exit code 0. Output `Cleaning cache...` and `Removed ...` for each existing cache directory.

### 29. `auto-lint update`
**Success Indicator:** Exit code 0. Output `Updating adapters...` and for each adapter (ruff, mypy, bandit, radon) either `updated` or `update failed` (non-fatal) appears.

### 30. `auto-lint stats test_project/src/`
**Success Indicator:** Exit code 0. Output displays the number of Python files, test files, and test ratio.

### 31. `auto-lint cancel <job_id_dummy>`
Since no job is running, execute with a dummy ID, e.g., `auto-lint cancel abc123`.
**Success Indicator:** Exit code 0. Output `Could not cancel job abc123 (not found or already finished)`.

### 32. `auto-lint plugins`
**Success Indicator:** Exit code 0. Output `No plugins or custom adapters found.` (or a list of plugins if any exist).

---

## Multi-Project & Batch Testing

### 33. `auto-lint batch test_project/src/bad.py test_project/src/style.py test_project/src/security.py`
**Success Indicator:** Exit code 1 (as one of the files fails). Output lists `PASSED`/`FAILED` status for each file.

### 34. `auto-lint multi-project test_project/src test_project`
**Success Indicator:** Exit code 0. Output contains a summary of `Multi-Project Scan Results` with average scores.

---

## Final Cleanup

### 35. `rm -rf test_project`
**Success Indicator:** Directory removal command succeeds. (No specific output needed.)

---

**End of Testing.**  
Create a final report summarizing:
- Total commands executed
- Number of successful vs. failed commands
- If any failures occurred, specify the command and the cause.

> **Note:** Some commands like `watch` require manual interruption (Ctrl+C). Simulate this by running in the background or using `timeout` (if available). For `cancel`, since no jobs are running, a "not found" output is considered success.
