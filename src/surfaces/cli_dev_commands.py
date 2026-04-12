"""Development CLI commands: diff, suggest, ignore, config, export."""
import asyncio
import click
import json
import os
import subprocess
from pathlib import Path
from agent.dependency_injection_container import get_container


def register_dev_commands(cli):

  @cli.command()
  @click.argument('path1', type=click.Path(exists=True))
  @click.argument('path2', type=click.Path(exists=True))
  @click.option('--output-format', type=click.Choice(['text', 'json']), default='text')
  def diff(path1, path2, output_format):
    """Compare lint results between two versions."""
    container = get_container()

    async def _diff():
      report1 = await container.analysis_use_case.execute(os.path.abspath(path1))
      report2 = await container.analysis_use_case.execute(os.path.abspath(path2))

      data1 = container.analysis_use_case.to_dict(report1)
      data2 = container.analysis_use_case.to_dict(report2)

      score_diff = data2['score'] - data1['score']
      status = " IMPROVED" if score_diff > 0 else " DECLINED" if score_diff < 0 else " UNCHANGED"

      if output_format == 'json':
        click.echo(json.dumps({
          'version1': {'score': data1['score'], 'path': path1},
          'version2': {'score': data2['score'], 'path': path2},
          'difference': score_diff,
          'status': status
        }))
      else:
        click.echo("Version Comparison:")
        click.echo(f" {path1}: {data1['score']:.1f}")
        click.echo(f" {path2}: {data2['score']:.1f}")
        click.echo(f" Difference: {score_diff:+.1f} {status}")

    asyncio.run(_diff())

  @cli.command()
  @click.argument('path', type=click.Path(exists=True))
  @click.option('--ai', is_flag=True, help='Use AI-powered suggestions')
  def suggest(path, ai):
    """AI-powered fix suggestions."""
    container = get_container()

    async def _suggest():
      click.echo(f" Analyzing {path} for suggestions...")
      report = await container.analysis_use_case.execute(os.path.abspath(path))
      data = container.analysis_use_case.to_dict(report)

      click.echo(f"\nSuggestions for {path}:")

      if data['score'] < 100:
        click.echo(f"  Governance score is {data['score']:.1f}/100")
        click.echo(f" → Run 'auto-lint fix {path}' to apply safe fixes")
        click.echo(" → Review remaining issues manually")
      else:
        click.echo("  Code is at 100.0 governance score!")

      if ai:
        click.echo("\n  AI suggestions: Coming soon (requires LLM integration)")

    asyncio.run(_suggest())

  @cli.command()
  @click.argument('rule')
  @click.option('--remove', is_flag=True, help='Remove rule from ignore list')
  @click.option('--path', default='.json', help='Config file path')
  def ignore(rule, remove, path):
    """Manage ignore rules in configuration."""
    config_file = Path(path)

    if not config_file.exists():
      click.echo(f" Config file not found: {path}")
      click.echo("Run 'auto-lint init' first")
      return

    config = json.loads(config_file.read_text())

    if 'ignored_rules' not in config:
      config['ignored_rules'] = []

    if remove:
      if rule in config['ignored_rules']:
        config['ignored_rules'].remove(rule)
        click.echo(f" Removed '{rule}' from ignore list")
      else:
        click.echo(f" '{rule}' not in ignore list")
    else:
      if rule not in config['ignored_rules']:
        config['ignored_rules'].append(rule)
        click.echo(f" Added '{rule}' to ignore list")
      else:
        click.echo(f" '{rule}' already ignored")

    config_file.write_text(json.dumps(config, indent=2))

  @cli.command()
  @click.argument('action', type=click.Choice(['show', 'edit', 'reset']))
  @click.option('--path', default='.json', help='Config file path')
  def config(action, path):
    """Edit configuration settings."""
    config_file = Path(path)

    if action == 'show':
      if not config_file.exists():
        click.echo(" Config not found. Run 'auto-lint init'")
        return
      click.echo(config_file.read_text())

    elif action == 'edit':
      editor = os.environ.get('EDITOR', 'nano')
      editor_base = os.path.basename(editor)
      allowed_editors = {'vim', 'nano', 'emacs', 'code', 'nvim', 'vi'}
      if editor_base not in allowed_editors:
        click.echo(f" Unknown editor '{editor_base}', opening anyway...")
      subprocess.run([editor, str(config_file)])
      click.echo(" Config saved")

    elif action == 'reset':
      if click.confirm("Reset config to defaults?"):
        default_config = {
          "project_name": "auto-linter",
          "thresholds": {"score": 80.0, "complexity": 10},
          "adapters": ["ruff", "mypy", "bandit", "radon"],
          "ignored_paths": ["node_modules", ".venv", "dist", "build"]
        }
        config_file.write_text(json.dumps(default_config, indent=2))
        click.echo(" Config reset to defaults")

  @cli.command()
  @click.argument('output_format', type=click.Choice(['sarif', 'junit', 'json']))
  @click.option('--output', '-o', help='Output file path')
  def export(output_format, output):
    """Export lint reports in different formats."""
    container = get_container()
    path = os.getcwd()

    async def _export():
      from capabilities.linting_report_formatters import to_sarif, to_junit

      report = await container.analysis_use_case.execute(os.path.abspath(path))
      data = container.analysis_use_case.to_dict(report)

      if output_format == 'sarif':
        result = to_sarif(data)
      elif output_format == 'junit':
        result = to_junit(data)
      else:
        result = json.dumps(data, indent=2)

      if output:
        Path(output).write_text(result)
        click.echo(f" Exported to {output}")
      else:
        click.echo(result)

    asyncio.run(_export())

  @cli.command()
  @click.option('--path', default='.', help='Project root directory')
  def init(path):
    """Initialize a new Auto-Linter configuration."""
    config_file = os.path.join(path, ".json")
    if os.path.exists(config_file):
      if not click.confirm(f"{config_file} already exists. Overwrite?"):
        return

    default_config = {
      "project_name": os.path.basename(os.path.abspath(path)),
      "thresholds": {
        "score": 80.0,
        "complexity": 10
      },
      "adapters": ["ruff", "mypy", "bandit", "radon", "duplicates", "trends"],
      "ignored_paths": ["node_modules", ".venv", "dist", "build"]
    }

    with open(config_file, "w") as f:
      json.dump(default_config, f, indent=4)
    click.echo(f" Initialized {config_file}")

  @cli.command()
  @click.option('--path', default='.', help='Project root directory')
  def install_hook(path):
    """Install git pre-commit hook."""
    container = get_container()
    if container.hooks_use_case.install():
      click.echo(" Pre-commit hook installed successfully.")
    else:
      click.echo(" Failed to install pre-commit hook.")

  @cli.command()
  @click.option('--path', default='.', help='Project root directory')
  def uninstall_hook(path):
    """Remove git pre-commit hook."""
    container = get_container()
    if container.hooks_use_case.uninstall():
      click.echo(" Pre-commit hook removed successfully.")
    else:
      click.echo(" Failed to remove pre-commit hook.")
