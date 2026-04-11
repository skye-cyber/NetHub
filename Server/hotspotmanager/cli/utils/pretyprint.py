from rich.console import Console
from rich.pretty import pprint as rich_pprint

console = Console()


def display_firewall_info(data):
    if not data:
        return

    console.rule("[bold cyan]AP Manager Firewall Info")
    rich_pprint(data, expand_all=True)
