"""
Device Monitor with TUI - Real-time network device monitoring
"""
import sys
import os
import time
import queue
import threading
import subprocess
from typing import Dict
from datetime import datetime

# Rich for TUI
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich import box
from rich.style import Style
from .config import Config
from .device import Device
from .netmonitor import NetworkScanner
from .datasources import DataSource, FileDataSource, APIDataSource
from .datasources import HAS_REQUESTS
from .writer import writer


# ==================== TUI Components ====================

class DeviceMonitorTUI:
    """Terminal UI for device monitoring"""

    def __init__(self, data_source: DataSource, scanner: NetworkScanner):
        self.data_source = data_source
        self.scanner = scanner
        self.console = Console()
        self.devices: Dict[str, Device] = {}
        self.running = True
        self.last_scan = datetime.now()
        self.interface_stats = {}
        self.event_queue = queue.Queue()

        # Start background threads
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.ui_thread = threading.Thread(target=self._ui_loop, daemon=True)

    def start(self):
        writer.write("Start all threads")
        """Start monitoring"""
        self.scan_thread.start()
        self.ui_thread.start()

        try:
            with Live(self._generate_layout(), refresh_per_second=4, screen=True) as live:
                while self.running:
                    try:
                        # Update UI
                        live.update(self._generate_layout())

                        # Check for user input
                        time.sleep(0.25)

                    except KeyboardInterrupt:
                        self.running = False
                        break
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")

        self.console.print("\n[yellow]Monitoring stopped[/yellow]")

    def _scan_loop(self):
        """Background scanning loop"""
        writer.write("Started scan thread")
        while self.running:
            try:
                self._perform_scan()
                writer.write(f"Loop Scan:\n{Config.SCAN_INTERVAL}")
                time.sleep(Config.SCAN_INTERVAL)
            except Exception as e:
                self.console.print(f"[red]Scan error: {e}[/red]")
                time.sleep(5)

    def _ui_loop(self):
        """Background UI update loop"""
        while self.running:
            try:
                # Process any UI events from queue
                pass
            except Exception:
                time.sleep(1)

    def _perform_scan(self):
        """Perform network scan and update devices"""
        # Get authenticated MACs
        auth_macs = set(self.data_source.get_authenticated_macs())

        # Scan network
        devices_data = self.scanner.scan_arp()
        writer.write(f"DATA: \n{devices_data}")

        # Update devices
        current_macs = set()
        for ip, mac, state in devices_data:
            current_macs.add(mac)

            if mac in self.devices:
                device = self.devices[mac]
                device.update()
            else:
                device = Device(ip, mac, mac in auth_macs, state)
                device.hostname = self.scanner.get_hostname(ip)
                device.vendor = self.scanner.get_vendor(mac)
                self.devices[mac] = device

            # Update IP if changed
            if self.devices[mac].ip != ip:
                self.devices[mac].ip = ip

        # Remove stale devices (not seen in current scan)
        stale_macs = set(self.devices.keys()) - current_macs
        for mac in stale_macs:
            # Keep for a while in case of intermittent connections
            if (datetime.now() - self.devices[mac].last_seen).seconds > 300:  # 5 minutes
                del self.devices[mac]

        # Update interface stats
        self.interface_stats = self.scanner.get_interface_stats()
        self.last_scan = datetime.now()
        writer.write(f"Devices UPD:\n{self.devices}")

    def _generate_layout(self) -> Layout:
        """Generate the TUI layout"""
        layout = Layout()

        # Split into header, main, and footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )

        # Header
        header_panel = Panel(
            Align.center(
                Text("📡 DEVICE MONITOR - Real-time Network Dashboard",
                     style="bold cyan"),
                vertical="middle"
            ),
            border_style="cyan"
        )
        layout["header"].update(header_panel)

        # Main content (split into left and right)
        layout["main"].split_row(
            Layout(name="devices", ratio=3),
            Layout(name="stats", ratio=2)
        )

        # Devices table
        devices_table = self._generate_devices_table()
        layout["devices"].update(
            Panel(
                devices_table,
                title=f"[bold]Connected Devices ({len(self.devices)})[/bold]",
                border_style="green",
                padding=(1, 1)
                # expand=True
            )
        )

        # Stats panel
        stats_panel = self._generate_stats_panel()
        layout["stats"].update(
            Panel(
                stats_panel,
                title="[bold]Network Statistics[/bold]",
                border_style="blue",
                padding=(1, 1)
            )
        )

        # Footer
        footer_text = Text()
        footer_text.append(" [Q]uit ", style="bold white on red")
        footer_text.append(" [A]uthenticate ", style="bold white on green")
        footer_text.append(" [B]lock ", style="bold white on #a16b00")
        footer_text.append(" [R]efresh ", style="bold white on blue")
        footer_text.append(f" Last scan: {self.last_scan.strftime('%H:%M:%S')} ",
                           style="dim white")

        layout["footer"].update(
            Panel(
                Align.center(footer_text),
                border_style="dim white"
            )
        )

        return layout

    def _generate_devices_table(self) -> Table:
        """Generate devices table"""
        table = Table(
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            expand=True
        )

        table.add_column("IP", style="cyan", width=19)
        table.add_column("MAC", style="#0055ff", width=20)
        table.add_column("Status", width=12)
        table.add_column("State", style="#ffff7f", width=12)
        table.add_column("Hostname", style="green", width=20)
        table.add_column("Vendor", style="yellow", width=20)
        table.add_column("Seen", style="dim white", width=9)

        # Sort devices by IP
        sorted_devices = sorted(self.devices.values(), key=lambda d: d.ip)

        for device in sorted_devices:
            # Status with color
            if device.authenticated:
                status = "[green]✓ AUTH[/green]"
            else:
                status = "[red]✗ BLOCKED[/red]"

            state = device.state

            # Hostname
            hostname = device.hostname or "Unknown"

            # Vendor (truncate if too long)
            vendor = device.vendor or "Unknown"
            if len(vendor) > 22:
                vendor = vendor[:19] + "..."

            # Last seen (relative time)
            seen_secs = (datetime.now() - device.last_seen).seconds
            if seen_secs < 60:
                seen = f"{seen_secs}s"
            elif seen_secs < 3600:
                seen = f"{seen_secs // 60}m"
            else:
                seen = f"{seen_secs // 3600}h"

            table.add_row(
                device.ip,
                device.mac,
                status,
                state,
                hostname,
                vendor,
                seen
            )

        return table

    def _generate_stats_panel(self) -> str:
        """Generate statistics panel content"""
        stats = []

        # Device counts
        auth_count = sum(1 for d in self.devices.values() if d.authenticated)
        blocked_count = len(self.devices) - auth_count

        stats.append(f"[bold]Devices:[/bold] {len(self.devices)} total")
        stats.append(f"  [green]✓ Authenticated:[/green] {auth_count}")
        stats.append(f"  [red]✗ Blocked:[/red] {blocked_count}")
        stats.append("")

        # Interface stats
        if self.interface_stats:
            rx_mb = self.interface_stats.get('rx_bytes', 0) / 1024 / 1024
            tx_mb = self.interface_stats.get('tx_bytes', 0) / 1024 / 1024

            stats.append(f"[bold]Interface {Config.INTERFACE}:[/bold]")
            stats.append(f"  RX: {rx_mb:.2f} MB ({self.interface_stats.get('rx_packets', 0)} packets)")
            stats.append(f"  TX: {tx_mb:.2f} MB ({self.interface_stats.get('tx_packets', 0)} packets)")
        else:
            stats.append("[yellow]Interface stats unavailable[/yellow]")

        stats.append("")

        # Data source info
        if isinstance(self.data_source, FileDataSource):
            stats.append(f"[dim]Data source: File ({Config.AUTH_FILE})[/dim]")
        else:
            stats.append(f"[dim]Data source: API ({Config.API_ENDPOINT})[/dim]")

        stats.append(f"[dim]Scan interval: {Config.SCAN_INTERVAL}s[/dim]")

        return "\n".join(stats)

    def toggle_device_auth(self, mac: str):
        """Toggle device authentication status"""
        if mac in self.devices:
            device = self.devices[mac]

            if device.authenticated:
                # Block device
                if self.data_source.block_device(mac):
                    device.authenticated = False
                    self.console.print(f"[yellow]Blocked device: {mac}[/yellow]")
            else:
                # Authenticate device
                if self.data_source.authenticate_device(mac):
                    device.authenticated = True
                    self.console.print(f"[green]Authenticated device: {mac}[/green]")

# ==================== Interactive CLI ====================


def interactive_cli():
    """Interactive command-line interface"""
    console = Console()

    # Choose data source
    console.print("\n[bold cyan]AP Manager Device Monitor[/bold cyan]")
    console.print("[dim]Real-time network device monitoring[/dim]\n")

    # Initialize data source
    if Config.USE_API and HAS_REQUESTS:
        data_source = APIDataSource(Config.API_ENDPOINT)
        console.print("[green]Using API data source[/green]")
    else:
        data_source = FileDataSource(Config.AUTH_FILE)
        console.print("[yellow]Using file data source[/yellow]")
        if Config.USE_API and not HAS_REQUESTS:
            console.print("[red]Warning: requests module not installed[/red]")

    # Initialize scanner
    scanner = NetworkScanner(Config.INTERFACE, Config.SUBNET)

    # Start TUI
    monitor = DeviceMonitorTUI(data_source, scanner)

    try:
        console.clear()
        monitor.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

# ==================== Main Entry Point ====================


if __name__ == "__main__":
    # Check if running as root
    if os.geteuid() != 0:
        print("This script must be run as root")
        print("Try: sudo python device_monitor.py")
        sys.exit(1)

    # Check for required commands
    required_cmds = ["ip", "arp", "nslookup"]
    missing_cmds = []
    for cmd in required_cmds:
        if subprocess.run(["which", cmd], capture_output=True).returncode != 0:
            missing_cmds.append(cmd)

    if missing_cmds:
        print(f"Missing required commands: {', '.join(missing_cmds)}")
        sys.exit(1)

    # Run interactive CLI
    interactive_cli()
