import click
import os
import shutil
import subprocess
import sys
from pathlib import Path



def register_maintenance_commands(cli):

  @cli.command()
  @click.argument('path', type=click.Path(exists=True), default='.')
  def stats(path):
    """Show statistics dashboard."""
    abs_path = os.path.abspath(path)
    click.echo(f" Auto-Linter Statistics for {abs_path}")
    click.echo("=" * 50)

    py_files = list(Path(abs_path).rglob("*.py"))
    py_count = len(py_files)
    click.echo(f" Python files: {py_count}")

    test_files = [f for f in py_files if f.name.startswith("test_")]
    test_count = len(test_files)
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
          [sys.executable, '-m', 'pip', 'install', '--upgrade', adapter],
          capture_output=True, text=True, timeout=60
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

    config_found = False
    for cfg in ['.auto_linter.json', 'auto_linter.config.yaml', 'pyproject.toml']:
      path = Path(cfg)
      if path.exists():
        if cfg == 'pyproject.toml':
          with open(path, 'r') as f:
            if '[tool.auto_linter]' in f.read():
              click.echo(f"  Config found: {cfg}")
              config_found = True
              break
        else:
          click.echo(f"  Config found: {cfg}")
          config_found = True
          break
    
    if not config_found:
      click.echo("  No config file found")
      issues.append("no config file")

    adapters = ['ruff', 'mypy', 'bandit', 'radon']
    venv_bin = os.path.dirname(sys.executable)
    
    for adapter in adapters:
      # Try system path first
      found = shutil.which(adapter)
      
      # Try venv bin if not found in system path
      if not found:
          adapter_path = os.path.join(venv_bin, adapter)
          if os.path.exists(adapter_path):
              found = adapter_path

      if found:
        click.echo(f"  {adapter} found at {found}")
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
    import asyncio
    from agent.tracking_job_registry import cancel_job
    
    ok = asyncio.run(cancel_job(job_id))
    if ok:
      click.echo(f"Job {job_id} cancelled successfully")
    else:
      click.echo(f"Could not cancel job {job_id} (not found or already finished)")
