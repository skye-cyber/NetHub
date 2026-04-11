import click
from rich.console import Console
from shared import cli

from captive_portal.monitoring.tui import interactive_cli

console = Console()


@cli.group()
def monitor():
    """Monitor network and devices"""
    pass


@monitor.command('devices')
@click.pass_context
def device(ctx):
    return interactive_cli()


