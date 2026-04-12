"""Core CLI commands: cli, check, scan, fix, report, version, adapters, security."""
import asyncio
import click
import json
import os
from agent.dependency_injection_container import get_container


@click.group()
def cli():
  """Auto-Linter CLI: Autonomous Code Quality Gatekeeper."""
  pass


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--git-diff', is_flag=True, help='Only lint files changed in this branch (vs main/master)')
def check(path, git_diff):
  """Run all linters and check governance score."""
  container = get_container()
  abs_path = os.path.abspath(path)

  # Git diff awareness: only lint changed files
  if git_diff:
    import subprocess
    try:
      # Get list of changed files compared to main/master
      result = subprocess.run(
        ['git', 'diff', '--name-only', 'origin/main...HEAD', 'HEAD...origin/main', 'main...HEAD', 'master...HEAD'],
        capture_output=True, text=True, cwd=abs_path, timeout=30
      )
      changed_files = []
      for line in result.stdout.strip().split('\n'):
        if line.strip() and not line.startswith(' '):
          changed_files.append(line.strip())
      
      if not changed_files:
        # Fallback: try just --name-only
        result = subprocess.run(
          ['git', 'diff', '--name-only', 'HEAD'],
          capture_output=True, text=True, cwd=abs_path, timeout=30
        )
        changed_files = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
      
      if changed_files:
        click.echo(f"Git diff mode: Checking {len(changed_files)} changed file(s)...")
        # Filter path to only include changed files
        abs_path = ' '.join(changed_files) if len(changed_files) <= 5 else changed_files[0]
        # Check only first few files for display
        for f in changed_files[:5]:
          click.echo(f"  + {f}")
        if len(changed_files) > 5:
          click.echo(f"  ... and {len(changed_files) - 5} more")
    except Exception as e:
      click.echo(f"Warning: Could not get git diff: {e}")

  async def _check():
    click.echo(f" Running analysis on {abs_path}...")
    report = await container.analysis_use_case.execute(abs_path)
    data = container.analysis_use_case.to_dict(report)

    click.echo(f"Score: {data['score']:.1f}/100.0")
    for source, results in data.items():
      if source in ["score", "summary", "is_passing", "governance"]:
        continue
      if not isinstance(results, list):
        continue

      status = " CLEAN" if not results else f" {len(results)} ISSUES"
      click.echo(f"[{source}] {status}")
      for res in results[:5]:
        click.echo(f" - {res['file']}:{res['line']} {res['code']}: {res['message']}")
      if len(results) > 5:
        click.echo(f" ... and {len(results)-5} more")

  asyncio.run(_check())


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--git-diff', is_flag=True, help='Only lint files changed in this branch')
def scan(path, git_diff):
  """Full deep scan of a directory (alias for check)."""
  ctx = click.get_current_context()
  ctx.invoke(check, path=path)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def fix(path):
  """Apply safe fixes automatically (Ruff, ESLint, Prettier)."""
  container = get_container()
  abs_path = os.path.abspath(path)

  async def _fix():
    click.echo(f" Applying safe fixes to {abs_path}...")
    results = await container.fixes_use_case.execute(abs_path)
    click.echo(results)

  asyncio.run(_fix())


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--output-format', type=click.Choice(['text', 'json', 'sarif', 'junit']), default='text')
def report(path, output_format):
  """Generate a detailed quality report."""
  container = get_container()
  abs_path = os.path.abspath(path)

  async def _report():
    report = await container.analysis_use_case.execute(abs_path)
    data = container.analysis_use_case.to_dict(report)

    if output_format == 'json':
      click.echo(json.dumps(data, indent=2))
    elif output_format == 'sarif':
      from capabilities.linting_report_formatters import to_sarif
      click.echo(to_sarif(data))
    elif output_format == 'junit':
      from capabilities.linting_report_formatters import to_junit
      click.echo(to_junit(data))
    else:
      click.echo(f"--- Quality Report for {abs_path} ---")
      click.echo(f"Governance Score: {data['score']:.1f}")
      for source, results in data.items():
        if source in ["score", "summary", "is_passing"]:
          continue
        if not isinstance(results, list):
          continue

        status = " CLEAN" if not results else f" {len(results)} ISSUES"
        click.echo(f"[{source}] {status}")
        for res in results:
          click.echo(f" - {res['file']}:{res['line']} {res['code']}: {res['message']}")

  asyncio.run(_report())


@cli.command()
def version():
  """Show version information."""
  click.echo("Auto-Linter v1.0.0 (AES Semantic Builder)")


@cli.command()
def adapters():
  """List enabled adapters."""
  container = get_container()
  click.echo("Enabled Adapters:")
  for adapter in container.adapters:
    click.echo(f" - {adapter.name()}")


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def security(path):
  """Run security-focused scan (Bandit, etc.)."""
  container = get_container()
  abs_path = os.path.abspath(path)

  async def _security():
    click.echo(f" Running security scan on {abs_path}...")
    report = await container.analysis_use_case.execute(abs_path)
    data = container.analysis_use_case.to_dict(report)

    bandit_results = data.get("bandit", [])
    if not bandit_results:
      click.echo(" No security vulnerabilities found.")
    else:
      click.echo(f" Found {len(bandit_results)} vulnerabilities.")
      for res in bandit_results:
        click.echo(f" - {res['file']}:{res['line']} {res['code']}: {res['message']} (Severity: {res['severity']})")

  asyncio.run(_security())


@cli.command()
@click.option('--base', default='HEAD', help='Git ref to compare from (default: HEAD)')
@click.option('--output-format', type=click.Choice(['text', 'json']), default='text')
def git_diff(base, output_format):
  """Show files changed since base ref (git diff awareness)."""
  container = get_container()
  diff = container.get_git_diff(base=base)
  if diff is None:
    click.echo(" Not a git repository or git not available.")
    return

  files = diff["lintable_files"]

  if output_format == 'json':
    click.echo(json.dumps(diff, indent=2))
  else:
    if not diff["all_files"]:
      click.echo(" No changed files detected.")
      return
    click.echo(f" Changed files since {base}:")
    if diff["added"]:
      click.echo(f"  Added ({len(diff['added'])}):")
      for f in diff["added"]:
        click.echo(f"    + {f}")
    if diff["modified"]:
      click.echo(f"  Modified ({len(diff['modified'])}):")
      for f in diff["modified"]:
        click.echo(f"    ~ {f}")
    if diff["deleted"]:
      click.echo(f"  Deleted ({len(diff['deleted'])}):")
      for f in diff["deleted"]:
        click.echo(f"    - {f}")
    if diff["renamed"]:
      click.echo(f"  Renamed ({len(diff['renamed'])}):")
      for r in diff["renamed"]:
        click.echo(f"    {r['old']} -> {r['new']}")
    click.echo(f"\n Lintable files: {len(files)}")


@cli.command()
def plugins():
  """List discovered and registered plugins."""
  container = get_container()
  discovered = container.get_discovered_plugins()
  if discovered:
    click.echo("Discovered Plugins:")
    for name, cls in discovered.items():
      click.echo(f"  {name}: {cls.__module__}.{cls.__name__}")

  custom = container.get_custom_adapters()
  if custom:
    click.echo("\nRegistered Custom Adapters:")
    for info in custom:
      click.echo(f"  {info['name']}: {info['class']}")

  if not discovered and not custom:
    click.echo("No plugins or custom adapters found.")
    click.echo("\nTo register a plugin, add entry point in pyproject.toml:")
    click.echo('  [project.entry-points."auto_linter.adapters"]')
    click.echo('  my_adapter = my_package:MyAdapterClass')


@cli.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('--output-format', type=click.Choice(['text', 'json']), default='text')
@click.option('--config', '-c', help='Config file with multi_project_paths')
def multi_project(paths, output_format, config):
  """Run lint across multiple projects and aggregate results."""
  import asyncio
  from pathlib import Path as P
  from agent.multi_project_orchestrator import load_multi_project_config
  from agent.dependency_injection_container import get_container

  project_list = list(paths)
  if not project_list:
    config_path = P(config) if config else None
    project_list = load_multi_project_config(config_path)
    if not project_list:
      project_list = [os.getcwd()]

  async def _multi():
    container = get_container()
    report = await container.multi_project.scan_all_projects(
      [P(p) for p in project_list]
    )
    if output_format == 'json':
      click.echo(json.dumps(report.to_dict(), indent=2))
    else:
      click.echo(report.to_text())

  asyncio.run(_multi())
