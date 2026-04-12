# DesktopCommander Integration Architecture

## 🎯 Overview

This document describes the **DesktopCommander Integration** architecture for auto_linter, where command execution is delegated to DesktopCommanderMCP for centralized security and auditing.

---

## 🏗️ Architecture

### Before (Direct Execution)
```
AI Agent → auto_linter MCP → subprocess.run() → System
                          ⚠️ SECURITY RISK!
```

### After (DesktopCommander Delegation)
```
AI Agent → auto_linter MCP → HTTP Request → DesktopCommanderMCP → System
                          ✅ CENTRALIZED SECURITY
```

---

## 🔧 Implementation

### auto_linter Changes

**File**: `src/auto_linter/surfaces/mcp/tools.py`

```python
import httpx

DESKTOP_COMMANDER_URL = os.environ.get(
    "DESKTOP_COMMANDER_URL", 
    "http://localhost:8080/execute"
)

@mcp.tool()
async def execute_command(action: str, args: dict | None = None):
    # ... validation logic ...
    
    # Build CLI command
    cli_cmd = ["auto-lint", normalized_action, path]
    
    # 🔒 Delegate to DesktopCommander
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            DESKTOP_COMMANDER_URL,
            json={
                "command": cli_cmd,
                "working_dir": str(Path.cwd()),
                "timeout": 300
            }
        )
        result = response.json()
        
        return json.dumps({
            "command": " ".join(cli_cmd),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "returncode": result.get("returncode", 1),
            "executed_by": "DesktopCommanderMCP"  # Audit trail
        })
```

---

## 📋 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DESKTOP_COMMANDER_URL` | `http://localhost:8080/execute` | DesktopCommander endpoint |

### Setup

```bash
# 1. Start DesktopCommanderMCP
cd /persistent/home/raka/mcp-servers/DesktopCommanderMCP
uv run desktop-commander --port 8080

# 2. Start auto_linter MCP
cd /persistent/home/raka/mcp-servers/auto_linter
export DESKTOP_COMMANDER_URL="http://localhost:8080/execute"
uv run auto-linter
```

---

## 🔐 Security Benefits

### Centralized Security

| Security Feature | Before | After |
|-----------------|--------|-------|
| **Command Validation** | Each MCP server | DesktopCommander only |
| **Path Validation** | Each MCP server | DesktopCommander only |
| **Audit Logging** | Each MCP server | Centralized logs |
| **Sandboxing** | Each MCP server | DesktopCommander only |
| **Rate Limiting** | Each MCP server | DesktopCommander only |

### Attack Surface Reduction

**Before**:
- 10 MCP servers = 10 attack surfaces
- Each needs security implementation
- Hard to audit

**After**:
- 10 MCP servers → 1 attack surface (DesktopCommander)
- Centralized security implementation
- Easy to audit

---

## 📊 Request/Response Flow

### Request to DesktopCommander

```json
POST http://localhost:8080/execute
Content-Type: application/json

{
  "command": ["auto-lint", "check", "/home/project/src/"],
  "working_dir": "/home/project",
  "timeout": 300
}
```

### Response from DesktopCommander

```json
{
  "stdout": "🔍 Running analysis...\nScore: 95.5/100.0",
  "stderr": "",
  "returncode": 0,
  "execution_time": 2.34
}
```

---

## 🛡️ Security Features (DesktopCommander)

DesktopCommander provides:

1. **Command Whitelist**
   ```json
   {
     "allowed_commands": ["auto-lint", "ruff", "mypy", ...]
   }
   ```

2. **Path Validation**
   ```python
   # Prevent path traversal
   if not path.startswith(allowed_root):
       raise SecurityError("Path outside allowed directory")
   ```

3. **Audit Logging**
   ```json
   {
     "timestamp": "2026-03-16T10:30:00Z",
     "user": "ai-agent",
     "command": "auto-lint check src/",
     "result": "success"
   }
   ```

4. **Rate Limiting**
   ```python
   # Max 10 commands per minute
   if rate_limiter.check_limit(user_id):
       raise RateLimitError()
   ```

5. **Sandboxing**
   ```bash
   # Run in Docker container
   docker run --rm --read-only auto-linter
   ```

---

## 📈 Benefits

### For auto_linter

| Benefit | Description |
|---------|-------------|
| **Simpler Code** | No subprocess management |
| **Better Security** | DesktopCommander handles it |
| **Easier Testing** | Mock HTTP calls |
| **Focus on Linting** | Core competency |

### For Users

| Benefit | Description |
|---------|-------------|
| **Centralized Audit** | One log for all commands |
| **Better Security** | Professional security implementation |
| **Easier Configuration** | One place to configure security |
| **Compliance** | Easier to meet security requirements |

---

## 🔍 Troubleshooting

### Error: "Cannot connect to DesktopCommanderMCP"

**Cause**: DesktopCommander not running

**Solution**:
```bash
# Start DesktopCommander
cd /persistent/home/raka/mcp-servers/DesktopCommanderMCP
uv run desktop-commander --port 8080
```

### Error: "Command timed out"

**Cause**: Command took > 5 minutes

**Solution**:
```bash
# Increase timeout in auto_linter
export DESKTOP_COMMANDER_TIMEOUT=600  # 10 minutes
```

### Error: "Command not in whitelist"

**Cause**: DesktopCommander security blocking command

**Solution**:
```bash
# Add command to DesktopCommander whitelist
# Edit DesktopCommander config file
```

---

## 🎯 Migration Guide

### For Existing auto_linter Users

1. **Install DesktopCommander** (if not already installed)
   ```bash
   cd /persistent/home/raka/mcp-servers/DesktopCommanderMCP
   uv pip install -e .
   ```

2. **Start DesktopCommander**
   ```bash
   uv run desktop-commander --port 8080
   ```

3. **Update auto_linter config**
   ```bash
   export DESKTOP_COMMANDER_URL="http://localhost:8080/execute"
   ```

4. **Test integration**
   ```bash
   uv run auto-lint check src/
   ```

---

## 📝 Future Enhancements

1. **WebSocket Support**
   - Real-time command output streaming
   - Better for long-running commands

2. **Batch Commands**
   - Execute multiple commands in one request
   - Better performance

3. **Command Queuing**
   - Queue commands for later execution
   - Better resource management

4. **Multi-User Support**
   - User authentication
   - Per-user quotas

---

## 🏆 Conclusion

The DesktopCommander integration provides:

✅ **Better Security** - Centralized, professional implementation  
✅ **Simpler Code** - auto_linter focuses on linting  
✅ **Easier Auditing** - One place for all logs  
✅ **Better Compliance** - Easier to meet security requirements  

**This is the recommended architecture for all MCP servers that need system access.**
