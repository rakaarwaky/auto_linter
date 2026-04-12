"""Maintenance CLI commands: stats, clean, update, doctor, cancel."""
import click
import json
import shutil
import subprocess
import sys
from pathlib import Path

from surfaces.mcp_execute_command import _running_jobs


def register_maintenance_commands(cli):

  @cli.command()
  def stats():
    """Show statistics dashboard."""
    click.echo(" Auto-Linter Statistics")
    click.echo("=" * 50)

    result = subprocess.run(
      ['find', '.', '-name', '*.py', '-type', 'f'],
      capture_output=True, text=True
    )
    py_count = len(result.stdout.strip().split('\n'))
    click.echo(f" Python files: {py_count}")

    result = subprocess.run(
      ['find', '.', '-name', 'test_*.py', '-type', 'f'],
      capture_output=True, text=True
    )
    test_count = len(result.stdout.strip().split('\n'))
    click.echo(f" Test files: {test_count}")

    if py_count > 0:
      click.echo(f" Test ratio: {test_count/py_count*100:.1f}%")
    else:
      click.echo(" Test ratio: N/A")
    click.echo("=" * 50)

  @cli.command()
  def clean():
    """Cleanup cache and temporary files."""
    click.echo(" Cleaning cache...")

    cache_dirs = ['.pytest_cache', '.mypy_cache', '.ruff_cache', '__pycache__', '.auto_linter_cache']
    cleaned = 0

    cwd = Path.cwd()
    if cwd.resolve() == Path('/').resolve():
      click.echo("Refusing to clean from root directory")
      return

    for cache_dir in cache_dirs:
      path = Path(cache_dir)
      if path.exists():
        shutil.rmtree(path)
        cleaned += 1
        click.echo(f"  Removed {cache_dir}")

    click.echo(f" Cleanup complete: {cleaned} directories removed")

  @cli.command()
  def update():
    """Update linter adapters to latest versions."""
    click.echo(" Updating adapters...")

    adapters = ['ruff', 'mypy', 'bandit', 'radon']

    for adapter in adapters:
      click.echo(f" Checking {adapter}...")
      try:
        result = subprocess.run(
          ['pip', 'install', '--upgrade', adapter],
          capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
          click.echo(f"   {adapter} updated")
        else:
          click.echo(f"   {adapter} update failed")
      except Exception as e:
        click.echo(f"   {adapter}: {str(e)}")

    click.echo("\n Update complete")

  @cli.command()
  def doctor():
    """Diagnose common issues."""
    click.echo(" Auto-Linter Doctor")
    click.echo("=" * 50)

    issues = []

    click.echo(f" Python: {sys.version.split()[0]}")

    result = subprocess.run(
      [sys.executable, '-m', 'pip', 'show', 'auto-linter'],
      capture_output=True, text=True
    )
    if result.returncode == 0:
      click.echo("  Auto-linter installed")
    else:
      click.echo("  Auto-linter not installed")
      issues.append("auto-linter not installed")

    config_file = Path('.json')
    if config_file.exists():
      click.echo("  Config file found")
    else:
      click.echo("  Config file not found")
      issues.append("no config file")

    adapters = ['ruff', 'mypy', 'bandit', 'radon']
    for adapter in adapters:
      result = subprocess.run(['which', adapter], capture_output=True)
      if result.returncode == 0:
        click.echo(f"  {adapter} found")
      else:
        click.echo(f"  {adapter} not found")
        issues.append(f"{adapter} not installed")

    click.echo("=" * 50)

    if issues:
      click.echo(f"\n Found {len(issues)} issue(s):")
      for issue in issues:
        click.echo(f" - {issue}")
      click.echo("\nRun 'auto-lint update' to fix missing adapters")
    else:
      click.echo("\n All systems healthy!")

  @cli.command()
  @click.argument('job_id')
  def cancel(job_id):
    """Cancel a running lint job."""
    if job_id not in _running_jobs:
      click.echo(f"Job '{job_id}' not found")
      return
    job_info = _running_jobs[job_id]
    if job_info["status"] in ("completed", "failed", "cancelled"):
      click.echo(f"Job already {job_info['status']}")
      return
    _running_jobs[job_id]["status"] = "cancelled"
    _running_jobs[job_id]["completed_at"] = "now"
    click.echo(f"Job {job_id} cancelled successfully")
