"""Analysis CLI commands: complexity, duplicates, trends, ci, batch, dependencies."""
import asyncio
import click
import os
import sys
from agent.dependency_injection_container import get_container


def register_analysis_commands(cli):
  """Register analysis commands with the CLI group."""

  @cli.command()
  @click.argument('path', type=click.Path(exists=True))
  def complexity(path):
    """Run cyclomatic complexity analysis."""
    container = get_container()
    abs_path = os.path.abspath(path)

    async def _complexity():
      click.echo(f" Analyzing complexity in {abs_path}...")
      report = await container.analysis_use_case.execute(abs_path)
      data = container.analysis_use_case.to_dict(report)

      complexity_results = data.get("radon", [])
      if not complexity_results:
        click.echo(" Complexity is within healthy limits.")
      else:
        click.echo(f" Found {len(complexity_results)} high complexity functions.")
        for res in complexity_results:
          click.echo(f" - {res['file']}:{res['line']} {res['message']}")

    asyncio.run(_complexity())

  @cli.command()
  @click.argument('path', type=click.Path(exists=True))
  def duplicates(path):
    """Find code duplication or oversized files."""
    container = get_container()
    abs_path = os.path.abspath(path)

    async def _duplicates():
      click.echo(f" Scanning for duplicates in {abs_path}...")
      report = await container.analysis_use_case.execute(abs_path)
      data = container.analysis_use_case.to_dict(report)

      dupe_results = data.get("duplicates", [])
      if not dupe_results:
        click.echo(" No major duplication issues detected.")
      else:
        for res in dupe_results:
          click.echo(f" - {res['file']}:{res['line']} {res['message']}")

    asyncio.run(_duplicates())

  @cli.command()
  @click.argument('path', type=click.Path(exists=True))
  def trends(path):
    """Show quality trends over time."""
    container = get_container()
    abs_path = os.path.abspath(path)

    async def _trends():
      report = await container.analysis_use_case.execute(abs_path)
      data = container.analysis_use_case.to_dict(report)

      trend_results = data.get("trends", [])
      if not trend_results:
        click.echo(" Quality trend: STABLE or IMPROVING")
      else:
        for res in trend_results:
          click.echo(f" {res['message']}")

    asyncio.run(_trends())

  @cli.command()
  @click.argument('path', type=click.Path(exists=True))
  @click.option('--exit-zero', is_flag=True, help="Always return exit code 0")
  def ci(path, exit_zero):
    """CI-optimized scan with exit codes."""
    container = get_container()
    abs_path = os.path.abspath(path)

    async def _ci():
      report = await container.analysis_use_case.execute(abs_path)
      data = container.analysis_use_case.to_dict(report)

      click.echo(f"CI Scan: score={data['score']:.1f}, passing={data['is_passing']}")
      if not data['is_passing'] and not exit_zero:
        sys.exit(1)

    asyncio.run(_ci())

  @cli.command()
  @click.argument('paths', nargs=-1, type=click.Path(exists=True))
  def batch(paths):
    """Run check on multiple paths."""
    if not paths:
      click.echo("No paths provided.")
      return

    container = get_container()
    all_passing = True

    async def _batch():
      nonlocal all_passing
      for path in paths:
        abs_path = os.path.abspath(path)
        click.echo(f"Checking {abs_path}...")
        report = await container.analysis_use_case.execute(abs_path)
        if not report.is_passing:
          all_passing = False
          click.echo(f" FAILED: {abs_path}")
        else:
          click.echo(f" PASSED: {abs_path}")

    asyncio.run(_batch())
    if not all_passing:
      sys.exit(1)

  @cli.command()
  @click.argument('path', type=click.Path(exists=True))
  def dependencies(path):
    """Scan for dependency vulnerabilities (pip-audit)."""
    container = get_container()
    abs_path = os.path.abspath(path)

    async def _dependencies():
      click.echo(f" Scanning for dependency vulnerabilities in {abs_path}...")
      report = await container.analysis_use_case.execute(abs_path)
      data = container.analysis_use_case.to_dict(report)

      dep_results = data.get("pip-audit", [])
      if not dep_results:
        click.echo(" No dependency vulnerabilities found.")
      else:
        click.echo(f" Found {len(dep_results)} vulnerable packages.")
        for res in dep_results:
          click.echo(f" - {res['message']} (Severity: {res['severity']})")

    asyncio.run(_dependencies())
