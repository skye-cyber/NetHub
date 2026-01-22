#!/usr/bin/env python
"""
AP Manager CLI - Modernized with Click and Rich
"""

import os
import sys
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
# from rich import print as rprint
# Local imports
from ap_manager import ApManager
from ap_utils.config import ConfigManager
from captive_portal.core.captive_entry import Captive
from captive_portal.core.config import BaseConfig
from captive_portal.monitoring.tui import interactive_cli
from captive_portal.core.config import baseconfig as firewallconfig

console = Console()
version = "1.0.2"

# ==================== CLI Setup ====================


class APManagerCLI:
    """Main CLI controller"""

    def __init__(self):
        self.manager = ApManager()
        self.config_manager = None
        self.captive = None

    def load_config(self, config_file: Optional[str] = None):
        """Load configuration"""
        if config_file and Path(config_file).exists():
            self.config_manager = ConfigManager(config_file)
        else:
            self.config_manager = ConfigManager()

        # Initialize captive portal with config
        self.captive = Captive(BaseConfig(config_file=config_file))

    def update_config(self, **kwargs):
        """Update configuration with provided values"""
        if not self.config_manager:
            self.load_config()

        # Filter out None values
        updates = {k: v for k, v in kwargs.items() if v is not None}

        if updates:
            # Update main config
            self.config_manager._dict_update(self.config_manager.get_config, updates)
            self.config_manager.save_config()

            # Update hostapd config if relevant keys
            hostapd_keys = {'ssid', 'password', 'channel', 'wpa_version', 'hidden'}
            if any(k in hostapd_keys for k in updates):
                hostman = ConfigManager(self.config_manager.__bconfdir__ / 'hostapd.json')
                hostman._dict_update(None, updates)
                hostman.save_config()

            # Update network config if relevant keys
            network_keys = {'wifi_iface', 'internet_iface', 'gateway', 'share_method'}
            if any(k in network_keys for k in updates):
                netman = ConfigManager(self.config_manager.__bconfdir__ / 'netconf.json')
                netman._dict_update(None, updates)
                netman.save_config()

            console.print("[green]✓ Configuration updated[/green]")

# ==================== CLI Commands ====================


@click.group(invoke_without_command=True)
@click.option('--config', '-c', type=click.Path(exists=True),
              help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """AP Manager - Hotspot and Captive Portal Management"""
    ctx.ensure_object(dict)
    ctx.obj['cli'] = APManagerCLI()
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = config

    # Load config
    ctx.obj['cli'].load_config(config)

    # Show help if no subcommand
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

# ==================== HOTSPOT COMMANDS ====================


@cli.group()
def hotspot():
    """Hotspot management commands"""
    pass


@hotspot.command('start')
@click.option('--wifi-iface', default='wlan0', help='WiFi interface to use')
@click.option('--internet-iface', default='wlan0', help='Internet-facing interface')
@click.option('--ssid', help='SSID for the hotspot')
@click.option('--password', help='Password for the hotspot')
@click.option('--channel', default=6, type=int, help='Channel number')
@click.option('--share-method', type=click.Choice(['nat', 'bridge', 'none']),
              default='nat', help='Internet sharing method')
@click.option('--no-virt', is_flag=True, help='Do not create virtual interface')
@click.option('--daemon', '-d', is_flag=True, help='Run in background')
@click.pass_context
def hotspot_start(ctx, wifi_iface, internet_iface, ssid, password, channel,
                  share_method, no_virt, daemon):
    """Start the hotspot"""
    cli_obj = ctx.obj['cli']

    # Update config with CLI options
    updates = {
        'wifi_iface': wifi_iface,
        'internet_iface': internet_iface,
        'ssid': ssid,
        'password': password,
        'channel': channel,
        'share_method': share_method,
        'no_virt': no_virt,
        'daemon': daemon
    }
    cli_obj.update_config(**updates)

    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Starting hotspot...", total=None)

        # Start hotspot
        try:
            success = cli_obj.manager.setup_accesspoint()
            progress.update(task, completed=100)

            if success:
                console.print(Panel.fit(
                    "[bold green]✓ Hotspot started successfully![/bold green]\n\n"
                    f"[cyan]SSID:[/cyan] {ssid or 'From config'}\n"
                    f"[cyan]Interface:[/cyan] {wifi_iface}\n"
                    f"[cyan]Sharing:[/cyan] {share_method} via {internet_iface}",
                    title="Hotspot Status"
                ))
            else:
                console.print("[red]✗ Failed to start hotspot[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@hotspot.command('stop')
@click.option('--force', '-f', is_flag=True, help='Force reply yes')
@click.pass_context
def hotspot_stop(ctx, force):
    """Stop the hotspot"""
    cli_obj = ctx.obj['cli']

    if force or Confirm.ask("Stop the hotspot?"):
        with console.status("[bold yellow]Stopping hotspot..."):
            success = cli_obj.manager.stop_accesspoint()

        if success:
            console.print("[green]✓ Hotspot stopped[/green]")
        else:
            console.print("[red]✗ Failed to stop hotspot[/red]")


@hotspot.command('status')
@click.pass_context
def hotspot_status(ctx):
    """Show hotspot status"""
    cli_obj = ctx.obj['cli']

    # Get running instances
    running = cli_obj.manager.network_config.get_running_instances()

    # Create status table
    table = Table(title="Hotspot Status", show_header=True, header_style="bold magenta")
    table.add_column("PID", style="cyan")
    table.add_column("Interface", style="blue")
    table.add_column("SSID", style="green")
    table.add_column("Clients", style="yellow")

    for instance in running:
        table.add_row(
            str(instance['pid']),
            instance.get('viface', 'N/A'),
            instance.get('ssid', 'N/A'),
            str(instance.get('clients', 0))
        )

    console.print(table)

    # Show interface info
    console.print("\n[bold]Network Interfaces:[/bold]")
    interfaces = cli_obj.manager.get_all_available_ifaces()
    for iface in interfaces:
        state_color = "green" if iface['state'] == 'UP' else "red"
        console.print(f"  • {iface['name']} [{state_color}]{iface['state']}[/{state_color}] ({iface['type']})")


@hotspot.command('interfaces')
@click.pass_context
def hotspot_interfaces(ctx):
    """List all available interfaces"""
    cli_obj = ctx.obj['cli']

    interfaces = cli_obj.manager.get_all_available_ifaces()

    table = Table(title="Available Interfaces", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("State", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("MAC", style="blue")
    table.add_column("IP Address", style="magenta")

    for iface in interfaces:
        table.add_row(
            iface['name'],
            iface['state'],
            iface['type'],
            iface.get('mac', 'N/A'),
            iface.get('ip', 'N/A')
        )

    console.print(table)

# ==================== FIREWALL COMMANDS ====================


@cli.group()
def firewall():
    """Firewall and captive portal management"""
    pass


@firewall.command('start')
@click.option('--config-file', type=click.Path(exists=True),
              help='Custom config file')
@click.pass_context
def firewall_start(ctx, config_file):
    """Start firewall and captive portal"""
    config_file = config_file or ctx.obj['config'] or '/etc/ap_manager/conf/config.json'

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


@firewall.command('stop')
@click.option('--config-file', type=click.Path(exists=True),
              help='Custom config file')
@click.pass_context
def firewall_stop(ctx, config_file):
    """Stop firewall and captive portal"""
    config_file = config_file or ctx.obj['config'] or '/etc/ap_manager/conf/config.json'

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


@firewall.command('status')
@click.option('--config-file', type=click.Path(exists=True),
              help='Custom config file')
@click.pass_context
def firewall_status(ctx, config_file):
    """Show firewall status"""
    config_file = config_file or ctx.obj['config'] or '/etc/ap_manager/conf/config.json'

    try:
        config = BaseConfig(config_file=config_file)
        captive = Captive(config)
        captive.status()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@firewall.command('debug')
@click.option('--config-file', type=click.Path(exists=True),
              help='Custom config file')
@click.pass_context
def firewall_debug(ctx, config_file):
    """Debug firewall and captive portal"""
    config_file = config_file or ctx.obj['config'] or '/etc/ap_manager/conf/config.json'

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


@fconfig.command('show')
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


@fconfig.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def firewall_config_set(ctx, key, value):
    """Set a configuration value"""
    new_conf = firewallconfig._dict_update_config({key: value})
    firewallconfig.save_config()
    firewallconfig.update_config(**new_conf)
    console.print(f"[green]✓ Set {key} = {value}[/green]")


@fconfig.command('edit')
@click.option('--editor', default=None, help='Editor to use')
@click.pass_context
def firewall_config_edit(ctx, editor):
    """Edit configuration file with text editor"""

    if firewallconfig:
        config_file = firewallconfig.config_file

        # Use provided editor or default
        editor = editor or os.environ.get('EDITOR', 'nano')

        os.system(f"{editor} {config_file}")
        console.print(f"[green]✓ Edited {config_file}[/green]")
    else:
        console.print("[red]No firewall configuration file loaded[/red]")


# ==================== CONFIG COMMANDS ====================


@cli.group()
def config():
    """AP Configuration management"""
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """Show current configuration"""
    cli_obj = ctx.obj['cli']

    if cli_obj.config_manager:
        config_data = cli_obj.config_manager.get_config

        console.print("[bold]Current Configuration:[/bold]")
        for key, value in config_data.items():
            if value:  # Skip empty values
                console.print(f"  [cyan]{key}:[/cyan] {value}")
    else:
        console.print("[yellow]No configuration loaded[/yellow]")


@config.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value"""
    cli_obj = ctx.obj['cli']

    cli_obj.update_config(**{key: value})
    console.print(f"[green]✓ Set {key} = {value}[/green]")


@config.command('edit')
@click.option('--editor', default=None, help='Editor to use')
@click.pass_context
def config_edit(ctx, editor):
    """Edit configuration file with text editor"""
    cli_obj = ctx.obj['cli']

    if cli_obj.config_manager:
        config_file = cli_obj.config_manager.config_file

        # Use provided editor or default
        editor = editor or os.environ.get('EDITOR', 'nano')

        os.system(f"{editor} {config_file}")
        console.print(f"[green]✓ Edited {config_file}[/green]")
    else:
        console.print("[red]No configuration file loaded[/red]")

# ==================== INFO COMMANDS ====================


@cli.command('version')
def show_version():
    """Show version information"""
    console.print(Panel.fit(
        f"[bold cyan]AP Manager[/bold cyan] v{version}\n"
        "[yellow]Hotspot and Captive Portal Management[/yellow]",
        title="Version"
    ))


@cli.command('info')
@click.pass_context
def system_info(ctx):
    """Show system information"""
    cli_obj = ctx.obj['cli']

    info_table = Table(title="System Information", show_header=False)
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="green")

    # Add info rows
    info_table.add_row("Prop", "Value", style="bold")
    info_table.add_section()
    info_table.add_row("Version", version)
    info_table.add_row("Python", sys.version.split()[0])
    info_table.add_row("Hostapd", "Available" if cli_obj.manager.has_hostapd else "Not found")

    # Interface count
    interfaces = cli_obj.manager.get_all_available_ifaces()

    wifi_count = sum(1 for i in interfaces if i['type'] == 'wireless')
    wired_count = sum(1 for i in interfaces if i['type'] == 'ethernet')
    bridge_count = sum(1 for i in interfaces if i['type'] == 'bridge')
    ap_count = sum(1 for i in interfaces if i['type'] == 'access point')

    info_table.add_section()
    info_table.add_row("Interface", "Count", style="bold")
    info_table.add_section()
    info_table.add_row("WiFi Interfaces", str(wifi_count))
    info_table.add_row("Wired Interfaces", str(wired_count))
    info_table.add_row("Bridge Interfaces", str(bridge_count))
    info_table.add_row("AP Interfaces", str(ap_count))

    console.print(info_table)


# ==================== MONITORING COMMANDS ====================

@cli.group()
def monitor():
    """Monitor network and devices"""
    pass


@monitor.command('devices')
@click.pass_context
def device(ctx):
    return interactive_cli()

# ==================== VALIDATION ====================


def validate_inputs(wifi_iface, internet_iface, share_method):
    """Validate command line inputs"""
    cli = APManagerCLI()

    # Check WiFi interface
    if not cli.manager.is_wifi_interface(wifi_iface):
        console.print(f"[red]ERROR: '{wifi_iface}' is not a WiFi interface[/red]")
        return False

    # Check AP support
    if not cli.manager.can_be_ap(wifi_iface):
        console.print("[red]ERROR: Your adapter does not support AP (master) mode[/red]")
        return False

    # Check internet interface for sharing
    if share_method != "none" and not cli.manager.is_interface(internet_iface):
        console.print(f"[red]ERROR: '{internet_iface}' is not an interface[/red]")
        return False

    return True

# ==================== MAIN ====================


def entry():
    try:
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

