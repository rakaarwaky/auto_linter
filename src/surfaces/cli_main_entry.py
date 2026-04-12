"""CLI entry point — registers all command groups."""
from surfaces.cli_core_commands import cli
from surfaces.cli_analysis_commands import register_analysis_commands
from surfaces.cli_dev_commands import register_dev_commands
from surfaces.cli_maintenance_commands import register_maintenance_commands
from surfaces.cli_watch_commands import register_watch_command
from surfaces.cli_setup_commands import setup

# Register all command groups
cli.add_command(setup)
register_analysis_commands(cli)
register_dev_commands(cli)
register_maintenance_commands(cli)
register_watch_command(cli)


def main():
    """Entry point for pip-installed auto-lint command."""
    cli()


if __name__ == "__main__":
    main()
