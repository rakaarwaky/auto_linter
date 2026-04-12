"""CLI command definitions - split into granular modules (max 300 lines each)."""
from surfaces.cli_core_commands import cli
from surfaces.cli_analysis_commands import register_analysis_commands
from surfaces.cli_dev_commands import register_dev_commands
from surfaces.cli_maintenance_commands import register_maintenance_commands
from surfaces.cli_watch_commands import register_watch_command

# Register all command groups
register_analysis_commands(cli)
register_dev_commands(cli)
register_maintenance_commands(cli)
register_watch_command(cli)
