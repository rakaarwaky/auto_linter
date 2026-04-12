"""Watch CLI command - file watcher with auto-lint on changes."""
import asyncio
import click
import os
import time


class LintHandler:
    """Lazy-imported watchdog handler to avoid startup errors."""
    def __init__(self, path):
      from watchdog.events import FileSystemEventHandler
      from agent.dependency_injection_container import get_container

      class _Handler(FileSystemEventHandler):
        def __init__(inner_self):
          self._path = path
          self._container = get_container()

        def on_modified(inner_self, event):
          if event.is_directory or not event.src_path.endswith(('.py', '.js', '.ts')):
            return
          click.echo(f"Re-checking {event.src_path}...")
          asyncio.run(inner_self._container.analysis_use_case.execute(event.src_path))

      self._handler = _Handler()


def register_watch_command(cli):
    @cli.command()
    @click.argument('path', type=click.Path(exists=True))
    def watch(path):
        """Watch for file changes and run linters automatically."""
        try:
            from watchdog.observers import Observer
        except ImportError:
            click.echo("Error: 'watchdog' is not installed. Run: pip install watchdog")
            return

        abs_path = os.path.abspath(path)
        click.echo(f" Watching {abs_path} for changes...")
        lint_handler = LintHandler(abs_path)
        observer = Observer()
        observer.schedule(lint_handler._handler, abs_path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
