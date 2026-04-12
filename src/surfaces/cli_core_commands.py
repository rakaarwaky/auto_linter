"""Core CLI commands: cli, check, scan, fix, report, version, adapters, security."""
import asyncio
import click
import json
import os
import sys
from pathlib import Path
from agent.dependency_injection_container import get_container


@click.group()
def cli():
  """Auto-Linter CLI: Autonomous Code Quality Gatekeeper."""
  pass


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def check(path):
  """Run all linters and check governance score."""
  container = get_container()
  abs_path = os.path.abspath(path)

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
@click.argument('path', type=click.Path(exists=True))
def scan(path):
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
@click.option('--format', type=click.Choice(['text', 'json', 'sarif', 'junit']), default='text')
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
  click.echo("Auto-Linter v0.1.0 (AES Semantic Builder)")


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
