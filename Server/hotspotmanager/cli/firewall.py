import os
import click
from rich.console import Console
from rich.prompt import Confirm

from shared import cli
from utils.pretyprint import display_firewall_info
from captive_portal.core.captive_entry import Captive
from captive_portal.core.config import BaseConfig
from captive_portal.core.config import baseconfig as firewallconfig

console = Console()


@cli.group()
def firewall():
    """Firewall and captive portal management"""
    pass


@firewall.command("start")
@click.option("--config-file", type=click.Path(exists=True), help="Custom config file")
@click.pass_context
def firewall_start(ctx, config_file):
    """Start firewall and captive portal"""
    config_file = config_file or ctx.obj["config"] or "/etc/ap_manager/conf/config.json"

    with console.status("[bold yellow]Starting firewall..."):
        try:
            config = BaseConfig(config_file=config_file)
            captive = Captive(config)
            success = captive.start()

            if success:
                console.print("[green]✓ Firewall and captive portal started[/green]")
            else:
                console.print("[red]✗ Failed to start firewall[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@firewall.command("stop")
@click.option("--config-file", type=click.Path(exists=True), help="Custom config file")
@click.pass_context
def firewall_stop(ctx, config_file):
    """Stop firewall and captive portal"""
    config_file = config_file or ctx.obj["config"] or "/etc/ap_manager/conf/config.json"

    if Confirm.ask("Stop firewall and captive portal?"):
        with console.status("[bold yellow]Stopping firewall..."):
            try:
                config = BaseConfig(config_file=config_file)
                captive = Captive(config)
                success = captive.stop()

                if success:
                    console.print("[green]✓ Firewall stopped[/green]")
                else:
                    console.print("[red]✗ Failed to stop firewall[/red]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")


@firewall.command("status")
@click.option("--config-file", type=click.Path(exists=True), help="Custom config file")
@click.pass_context
def firewall_status(ctx, config_file):
    """Show firewall status"""
    config_file = config_file or ctx.obj["config"] or "/etc/ap_manager/conf/config.json"

    try:
        config = BaseConfig(config_file=config_file)
        captive = Captive(config)
        result = captive.status()
        display_firewall_info(result)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@firewall.command("reset")
@click.option("--config-file", type=click.Path(exists=True), help="Custom config file")
@click.pass_context
def firewall_reset(ctx, config_file):
    """Show firewall status"""
    config_file = config_file or ctx.obj["config"] or "/etc/ap_manager/conf/config.json"

    try:
        config = BaseConfig(config_file=config_file)
        captive = Captive(config)
        result = captive.reset()
        display_firewall_info(result)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@firewall.command("debug")
@click.option("--config-file", type=click.Path(exists=True), help="Custom config file")
@click.pass_context
def firewall_debug(ctx, config_file):
    """Debug firewall and captive portal"""
    config_file = config_file or ctx.obj["config"] or "/etc/ap_manager/conf/config.json"

    with console.status("[bold yellow]Running debug..."):
        try:
            config = BaseConfig(config_file=config_file)
            captive = Captive(config)
            captive.debug()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@firewall.group()
def fconfig():
    """Firewall (+captive) Configuration management"""
    pass


@fconfig.command("show")
@click.pass_context
def firewall_config_show(ctx):
    """Show current configuration"""

    if firewallconfig:
        config_data = firewallconfig.get_config()

        console.print("[bold]Current Firewall Configuration:[/bold]")
        for key, value in config_data.items():
            if value:  # Skip empty values
                console.print(f"  [cyan]{key}:[/cyan] {value}")
    else:
        console.print("[yellow]No configuration loaded[/yellow]")


@fconfig.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def firewall_config_set(ctx, key, value):
    """Set a configuration value"""
    new_conf = firewallconfig._dict_update_config({key: value})
    firewallconfig.save_config()
    firewallconfig.update_config(**new_conf)
    console.print(f"[green]✓ Set {key} = {value}[/green]")


@fconfig.command("edit")
@click.option("--editor", default=None, help="Editor to use")
@click.pass_context
def firewall_config_edit(ctx, editor):
    """Edit configuration file with text editor"""

    if firewallconfig:
        config_file = firewallconfig.config_file

        # Use provided editor or default
        editor = editor or os.environ.get("EDITOR", "nano")

        os.system(f"{editor} {config_file}")
        console.print(f"[green]✓ Edited {config_file}[/green]")
    else:
        console.print("[red]No firewall configuration file loaded[/red]")
