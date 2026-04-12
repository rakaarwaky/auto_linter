"""CLI setup commands — init, doctor, mcp-config."""
import json
import platform
import shutil
from pathlib import Path

import click


@click.group()
def setup():
    """Setup and configuration commands."""
    pass


@setup.command()
def init():
    """Auto-configure auto-linter for your system."""
    click.echo("Auto-Linter Setup")
    click.echo("=" * 50)

    # 1. Detect environment
    click.echo("\n[1/4] Detecting environment...")
    home = str(Path.home())
    dc_socket = "/tmp/dc.sock"
    dc_http = "http://localhost:24680/execute"
    has_dc_socket = Path(dc_socket).exists()
    has_dc_http = _check_http(dc_http)

    if has_dc_socket:
        click.echo(f"  DesktopCommander: found (socket: {dc_socket})")
        transport = dc_socket
    elif has_dc_http:
        click.echo(f"  DesktopCommander: found (HTTP: {dc_http})")
        transport = dc_http
    else:
        click.echo("  DesktopCommander: not found (will use direct execution)")
        transport = "auto"

    click.echo(f"  Python: {platform.python_version()}")
    click.echo(f"  OS: {platform.system()} {platform.release()}")
    click.echo(f"  Home: {home}")

    # 2. Check linters
    click.echo("\n[2/4] Checking linters...")
    linters = {
        "ruff": shutil.which("ruff"),
        "mypy": shutil.which("mypy"),
        "eslint": shutil.which("eslint"),
        "prettier": shutil.which("prettier"),
    }
    for name, path in linters.items():
        status = "found" if path else "not found"
        click.echo(f"  {name}: {status}")

    # 3. Create .env
    click.echo("\n[3/4] Creating .env...")
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        click.echo("  .env already exists — skipping")
    else:
        env_content = _generate_env(transport, home)
        env_path.write_text(env_content)
        click.echo(f"  Created: {env_path}")

    # 4. Generate MCP config snippets
    click.echo("\n[4/4] MCP server configuration:")
    mcp_json = _generate_mcp_config(transport)
    click.echo("\n  For Claude Desktop / VS Code (mcp.json):")
    click.echo("  " + "-" * 45)
    for line in json.dumps(mcp_json, indent=4).split("\n"):
        click.echo(f"  {line}")

    click.echo("\n" + "=" * 50)
    click.echo("Setup complete!")
    click.echo("\nUsage:")
    click.echo("  auto-lint check ./src/          # run lint")
    click.echo("  auto-linter                     # start MCP server")
    click.echo("  auto-lint doctor                # diagnose issues")


@setup.command()
def doctor():
    """Diagnose configuration and dependencies."""
    click.echo("Auto-Linter Doctor")
    click.echo("=" * 50)

    issues = []

    # Check Python
    ver = platform.python_version_tuple()
    if int(ver[0]) < 3 or (int(ver[0]) == 3 and int(ver[1]) < 12):
        issues.append(f"Python >= 3.12 required, got {platform.python_version()}")
    else:
        click.echo(f"[OK] Python {platform.python_version()}")

    # Check core deps
    for pkg in ["mcp", "pydantic", "click", "yaml", "dotenv"]:
        try:
            __import__(pkg.replace("-", "_"))
            click.echo(f"[OK] {pkg}")
        except ImportError:
            issues.append(f"Missing dependency: {pkg}")
            click.echo(f"[!!] {pkg} — MISSING")

    # Check linters
    for name in ["ruff", "mypy"]:
        if shutil.which(name):
            click.echo(f"[OK] {name}")
        else:
            click.echo(f"[--] {name} — not installed (optional)")

    # Check DesktopCommander
    dc_socket = Path("/tmp/dc.sock")
    if dc_socket.exists():
        click.echo(f"[OK] DesktopCommander socket: {dc_socket}")
    else:
        click.echo("[--] DesktopCommander — not running (direct mode)")

    # Check config
    if Path(".env").exists():
        click.echo("[OK] .env exists")
    else:
        click.echo("[--] .env not found — run: auto-linter init")

    if Path("auto_linter.config.yaml").exists():
        click.echo("[OK] auto_linter.config.yaml exists")
    else:
        click.echo("[--] auto_linter.config.yaml not found (using defaults)")

    click.echo("\n" + "=" * 50)
    if issues:
        click.echo(f"Found {len(issues)} issue(s):")
        for issue in issues:
            click.echo(f"  - {issue}")
    else:
        click.echo("All checks passed!")


@setup.command("mcp-config")
@click.option("--client", type=click.Choice(["claude", "hermes", "vscode", "all"]), default="all")
def mcp_config(client):
    """Print MCP server configuration for various clients."""
    transport = "auto"
    if Path("/tmp/dc.sock").exists():
        transport = "/tmp/dc.sock"

    configs = {
        "claude": _mcp_config_claude(transport),
        "hermes": _mcp_config_hermes(transport),
        "vscode": _mcp_config_vscode(transport),
    }

    for name, config in configs.items():
        if client != "all" and client != name:
            continue
        click.echo(f"\n{'=' * 50}")
        click.echo(f"  {name.upper()} MCP Config")
        click.echo(f"{'=' * 50}")
        for line in json.dumps(config, indent=2).split("\n"):
            click.echo(f"  {line}")


@setup.command()
@click.option("--remove", is_flag=True, help="Remove auto-linter from Hermes config")
def hermes(remove):
    """Auto-install auto-linter into Hermes Agent."""
    import subprocess
    import shutil

    click.echo("Auto-Linter + Hermes Setup")
    click.echo("=" * 50)

    # Check if hermes is installed
    hermes_bin = shutil.which("hermes")
    if not hermes_bin:
        click.echo("\n[ERROR] hermes command not found!")
        click.echo("Install Hermes Agent first:")
        click.echo("  pip install hermes-agent")
        click.echo("  or: curl -sSL https://hermes.ai/install | bash")
        return

    click.echo(f"\n  Hermes: {hermes_bin}")

    # Check if auto-linter is installed
    auto_lint_bin = shutil.which("auto-linter")
    if not auto_lint_bin:
        click.echo("[ERROR] auto-linter command not found!")
        click.echo("Install auto-linter first:")
        click.echo("  pip install auto-linter")
        return

    click.echo(f"  auto-linter: {auto_lint_bin}")

    # Remove mode
    if remove:
        click.echo("\nRemoving auto-linter from Hermes...")
        result = subprocess.run(
            ["hermes", "mcp", "remove", "auto-linter"],
            capture_output=True, text=True,
        )
        click.echo(result.stdout or result.stderr)
        click.echo("Done!")
        return

    # Detect transport
    dc_socket = Path("/tmp/dc.sock")
    env_vars = []
    if dc_socket.exists():
        click.echo(f"  DesktopCommander: found ({dc_socket})")
        env_vars = ["DESKTOP_COMMANDER_URL=/tmp/dc.sock"]
    else:
        click.echo("  DesktopCommander: not found (direct mode)")

    # Add via hermes mcp add
    click.echo("\nAdding auto-linter to Hermes config...")
    cmd = ["hermes", "mcp", "add", "auto-linter", "--command", "auto-linter"]
    for e in env_vars:
        cmd.extend(["--env", e])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        click.echo(result.stdout or "  Added successfully!")
        click.echo("\n" + "=" * 50)
        click.echo("Done! Restart Hermes to use auto-linter:")
        click.echo("  hermes chat")
        click.echo("\nOr test the connection:")
        click.echo("  hermes mcp test auto-linter")
    else:
        click.echo(f"[ERROR] {result.stderr}")
        click.echo("\nManual fallback:")
        click.echo("  hermes mcp add auto-linter --command auto-linter")


# ── Helpers ────────────────────────────────────────────────────────

def _check_http(url: str) -> bool:
    """Quick HTTP health check."""
    try:
        import httpx
        resp = httpx.get(url.replace("/execute", "/health"), timeout=2.0)
        return resp.status_code < 500
    except Exception:
        return False


def _generate_env(transport: str, home: str) -> str:
    """Generate .env content."""
    lines = [
        "# Auto-Linter Environment Configuration",
        "# Generated by: auto-linter init",
        "",
        "# DesktopCommander transport:",
    ]
    if transport != "auto":
        lines.append(f"DESKTOP_COMMANDER_URL={transport}")
    else:
        lines.append("# DESKTOP_COMMANDER_URL=/tmp/dc.sock  # uncomment if available")
    lines.extend([
        "DESKTOP_COMMANDER_PORT=24680",
        "DESKTOP_COMMANDER_TIMEOUT=300",
        "",
        "# Phantom root (for JS/TS linters):",
        f"PHANTOM_ROOT={home}/",
    ])
    return "\n".join(lines) + "\n"


def _generate_mcp_config(transport: str) -> dict:
    """Generate mcp.json entry for auto-linter."""
    return {
        "auto-linter": {
            "command": "auto-linter",
            "args": [],
            "alwaysAllow": [
                "lint", "execute_command", "health_check",
                "list_commands", "read_skill_context",
            ],
        }
    }


def _mcp_config_claude(transport: str) -> dict:
    """Claude Desktop MCP config."""
    return {
        "mcpServers": _generate_mcp_config(transport)
    }


def _mcp_config_hermes(transport: str) -> dict:
    """Hermes MCP config."""
    entry = _generate_mcp_config(transport)["auto-linter"]
    if transport.startswith("/"):
        entry["env"] = {"DESKTOP_COMMANDER_URL": transport}
    return {"auto-linter": entry}


def _mcp_config_vscode(transport: str) -> dict:
    """VS Code MCP config."""
    return {
        "mcp": {
            "servers": _generate_mcp_config(transport)
        }
    }
