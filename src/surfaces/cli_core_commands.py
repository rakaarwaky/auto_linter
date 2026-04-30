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
  if not os.path.isabs(path):
    raise click.UsageError(f"Absolute path required. Got: '{path}'. AI Agents must provide full paths starting with '/'.")
  
  container = get_container()
  abs_path = os.path.abspath(path)

  if git_diff:
    import subprocess
    try:
      # Get default branch name dynamically
      default_branch = "main"
      try:
        branch_result = subprocess.run(
          ['git', 'symbolic-ref', 'refs/remotes/origin/HEAD'],
          capture_output=True, text=True, cwd=abs_path, timeout=10
        )
        if branch_result.returncode == 0:
          # refs/remotes/origin/HEAD -> refs/remotes/origin/main
          ref = branch_result.stdout.strip()
          if '/' in ref:
            default_branch = ref.split('/')[-1]
        else:
          # Fallback: try to detect from remote
          remote_result = subprocess.run(
            ['git', 'remote', 'show', 'origin'],
            capture_output=True, text=True, cwd=abs_path, timeout=10
          )
          for line in remote_result.stdout.split('\n'):
            if 'HEAD branch:' in line:
              default_branch = line.split(':')[1].strip()
              break
      except Exception:
        pass

      # Get list of changed files compared to default branch
      changed_files = []
      for variant in [f'origin/{default_branch}...HEAD', 
                      f'HEAD...origin/{default_branch}', 
                      f'{default_branch}...HEAD',
                      'master...HEAD']:
        result = subprocess.run(
          ['git', 'diff', '--name-only', variant],
          capture_output=True, text=True, cwd=abs_path, timeout=30
        )
        if result.returncode == 0:
          for line in result.stdout.strip().split('\n'):
            if line.strip() and not line.startswith(' '):
              changed_files.append(line.strip())
          if changed_files:
            break

      # Fallback: just use current changes
      if not changed_files:
        result = subprocess.run(
          ['git', 'diff', '--name-only', 'HEAD'],
          capture_output=True, text=True, cwd=abs_path, timeout=30
        )
        changed_files = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        
      if not changed_files:
        # Absolute last resort: list all modified/new files
        result = subprocess.run(
          ['git', 'ls-files', '--modified', '--others', '--exclude-standard'],
          capture_output=True, text=True, cwd=abs_path, timeout=30
        )
        changed_files = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        
      if changed_files:
        click.echo(f"Git diff mode: Checking {len(changed_files)} changed file(s)...")
        # Process each changed file individually
        for f in changed_files[:5]:
          click.echo(f"  + {f}")
        if len(changed_files) > 5:
          click.echo(f"  ... and {len(changed_files) - 5} more")
        
        # Process all changed files
        async def _check_all():
          total_results = {"score": 100.0, "is_passing": True}
          all_data = []
          for cf in changed_files:
            try:
              cf_abs = os.path.join(abs_path, cf)
              report = await container.analysis_use_case.execute(cf_abs)
              data = container.analysis_use_case.to_dict(report)
              all_data.append((cf, data))
              if data.get("is_passing") == False:
                total_results["is_passing"] = False
            except Exception as e:
              click.echo(f"  Error processing {cf}: {e}")
          
          # Aggregate scores
          if all_data:
            avg_score = sum(d[1].get("score", 0) for d in all_data) / len(all_data)
            total_results["score"] = round(avg_score, 1)
            total_results["files"] = len(all_data)
            
            # Collect all issues
            for cf, data in all_data:
              for source, results in data.items():
                if source in ["score", "summary", "is_passing", "governance"]:
                  continue
                if not isinstance(results, list):
                  continue
                if source not in total_results:
                  total_results[source] = []
                for res in results:
                  res_copy = dict(res)
                  res_copy["file"] = cf
                  total_results[source].append(res_copy)
          
          return total_results
        
        async def _check():
          data = await _check_all()
          click.echo(f"Score: {data['score']:.1f}/100.0")
          for source, results in data.items():
            if source in ["score", "summary", "is_passing", "files"]:
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
        return

    except Exception as e:
      click.echo(f"Warning: Could not get git diff: {e}")

  # Normal (non-git-diff) check path
  async def _check():
    click.echo(f" Running analysis on {abs_path}...")
    report = await container.analysis_use_case.execute(abs_path)
    data = container.analysis_use_case.to_dict(report)

    click.echo(f"Score: {data['score']:.1f}/100.0")
    for source, results in data.items():
      if source in ["score", "summary", "is_passing"]:
        continue
      if not isinstance(results, list):
        continue  # pragma: no cover

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
  if not os.path.isabs(path):
    raise click.UsageError(f"Absolute path required. Got: '{path}'.")
  ctx = click.get_current_context()
  ctx.invoke(check, path=path)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
def fix(path):
  """Apply safe fixes automatically (Ruff, ESLint, Prettier)."""
  if not os.path.isabs(path):
    raise click.UsageError(f"Absolute path required. Got: '{path}'.")
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
  if not os.path.isabs(path):
    raise click.UsageError(f"Absolute path required. Got: '{path}'.")
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
          continue  # pragma: no cover

        status = " CLEAN" if not results else f" {len(results)} ISSUES"
        click.echo(f"[{source}] {status}")
        for res in results:
          click.echo(f" - {res['file']}:{res['line']} {res['code']}: {res['message']}")

  asyncio.run(_report())


@cli.command()
def version():
  """Show version information."""
  click.echo("Auto-Linter v1.6.0 (AES Semantic Builder)")


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
