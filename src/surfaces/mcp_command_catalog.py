"""MCP Tools: list_commands and read_skill_context."""
from pathlib import Path


_COMMAND_CATALOG = {
    "check": {"description": "Run full governance analysis", "example": "auto-lint check /path"},
    "scan": {"description": "Deep directory scan (alias for check)", "example": "auto-lint scan ./src/"},
    "fix": {"description": "Apply safe fixes", "example": "auto-lint fix file.py"},
    "report": {"description": "Generate quality reports", "example": "auto-lint report ./src --format json"},
    "ci": {"description": "CI-optimized with exit codes", "example": "auto-lint ci /path --exit-zero"},
    "batch": {"description": "Check multiple paths", "example": "auto-lint batch path1.py path2.js"},
    "watch": {"description": "Watch files for changes", "example": "auto-lint watch ./src/"},
    "security": {"description": "Bandit vulnerability scanning", "example": "auto-lint security /path"},
    "complexity": {"description": "Cyclomatic complexity", "example": "auto-lint complexity ./src/"},
    "duplicates": {"description": "Code duplication detection", "example": "auto-lint duplicates /path"},
    "trends": {"description": "Quality trend over time", "example": "auto-lint trends ."},
    "dependencies": {"description": "Dependency vulnerability scan", "example": "auto-lint dependencies ."},
    "diff": {"description": "Compare two versions", "example": "auto-lint diff v1.py v2.py"},
    "suggest": {"description": "AI-powered suggestions", "example": "auto-lint suggest file.py"},
    "stats": {"description": "Statistics dashboard", "example": "auto-lint stats ./src/"},
    "init": {"description": "Initialize config", "example": "auto-lint init /path"},
    "config": {"description": "Edit configuration", "example": "auto-lint config get thresholds"},
    "ignore": {"description": "Manage ignore rules", "example": "auto-lint ignore add E501"},
    "import": {"description": "Import configurations", "example": "auto-lint import config.json"},
    "export": {"description": "Export reports", "example": "auto-lint export --format sarif"},
    "clean": {"description": "Cleanup cache", "example": "auto-lint clean"},
    "update": {"description": "Update adapters", "example": "auto-lint update"},
    "doctor": {"description": "Diagnose issues", "example": "auto-lint doctor"},
    "adapters": {"description": "List enabled adapters", "example": "auto-lint adapters"},
    "install-hook": {"description": "Install git pre-commit hook", "example": "auto-lint install-hook"},
    "uninstall-hook": {"description": "Remove git pre-commit hook", "example": "auto-lint uninstall-hook"},
    "cancel": {"description": "Cancel a running lint job", "example": "auto-lint cancel <job_id>"},
    "plugins": {"description": "List discovered and registered plugins", "example": "auto-lint plugins"},
    "multi-project": {"description": "Run lint across multiple projects", "example": "auto-lint multi-project proj1/ proj2/"},
    "version": {"description": "Show version", "example": "auto-lint version"},
}


async def list_commands(domain: str | None = None):
    """List all available CLI commands with descriptions and examples."""
    if domain:
        domain_key = domain.lower()
        commands = {k: v for k, v in _COMMAND_CATALOG.items() if domain_key in k}
        return {"domain": domain, "commands": commands}
    
    result = {}
    for command, info in _COMMAND_CATALOG.items():
        result[command] = {
            "description": info["description"], 
            "example_usage": info["example"]
        }
    return result


async def read_skill_context(section: str | None = None):
    """Read SKILL.md documentation sections or the entire file."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    skill_path = root_dir / "SKILL.md"
    
    if not skill_path.exists():
        return {"error": "SKILL.md not found", "path": str(skill_path)}
    
    try:
        content = skill_path.read_text(encoding="utf-8")
        
        # If no section specified, return the WHOLE file as requested
        if not section or section.lower() in ["all", "full", "entire", "skill.md"]:
            return {
                "section": "Full Documentation",
                "content": content.strip()
            }
            
        lines = content.splitlines()
        docs = {}
        current_title = "Introduction"
        current_section = "introduction"
        current_content = []
        
        for line in lines:
            if line.startswith("# ") or line.startswith("## "):
                if current_content:
                    docs[current_section] = {
                        "title": current_title,
                        "body": "\n".join(current_content).strip()
                    }
                current_title = line.lstrip("#").strip()
                current_section = current_title.lower()
                current_content = [line]
            else:
                current_content.append(line)
        
        if current_content:
            docs[current_section] = {
                "title": current_title,
                "body": "\n".join(current_content).strip()
            }
            
        query = section.lower()
        for key, data in docs.items():
            if query in key:
                return {
                    "section": data["title"],
                    "content": data["body"]
                }
                
        return {
            "error": f"Section '{section}' not found",
            "available_sections": [d["title"] for d in docs.values()]
        }
    except Exception as e:
        return {"error": f"Failed to read documentation: {str(e)}"}


def register_list_commands(mcp):
    mcp.tool()(list_commands)


def register_read_skill_context(mcp):
    mcp.tool()(read_skill_context)
