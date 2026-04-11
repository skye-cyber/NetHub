#!/usr/bin/env python
"""
AP Manager CLI - Modernized with Click and Rich
"""

import os
import sys
from rich.console import Console

version = "1.0.3"

console = Console()

# cli = click.CommandCollection(sources=[auth])


def entry():
    try:
        # Local imports
        import initializer
        import auth
        import hotspot
        import firewall
        import monitor
        from shared import cli
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        # if ctx.obj.get('verbose', False):
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    # Check for root privileges
    if os.geteuid() != 0:
        console.print("[bold red]This script must be run as root[/bold red]")
        console.print("[yellow]Try: sudo ap_manager --help[/yellow]")
        sys.exit(1)

    # Run CLI
    entry()
