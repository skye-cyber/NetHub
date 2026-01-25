"""
Device Monitor with TUI - Real-time network device monitoring
"""
import sys
import os
import time
import queue
import threading
import socket
import subprocess
from typing import Dict
from datetime import datetime
from collections import defaultdict

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
from .keyboard_handler import SimpleKeyboardHandler

# ==================== TUI Components ====================

class DeviceMonitorTUI:
    """Terminal UI for device monitoring"""

    def __init__(self, data_source: DataSource, scanner: NetworkScanner):
        self.data_source = data_source
        self.scanner = scanner
        self.console = Console()
        self.devices: Dict[str, Device] = {}
        self.devices_lock = threading.Lock()
        self.running = True
        self.last_scan = datetime.now()
        self.interface_stats = {}
        self.interface_stats_lock = threading.Lock()
        self.event_queue = queue.Queue()

        self.keyboard_handler = SimpleKeyboardHandler(self)

        self.selected_index = 0
        self.devices_list = []  # Cache for selection
        # self.input_thread = threading.Thread(target=self._input_loop, daemon=True)

        # Start background threads
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.ui_thread = threading.Thread(target=self._ui_loop, daemon=True)

    def start(self):
        writer.write("Start all threads")
        """Start monitoring"""
        self.scan_thread.start()
        self.ui_thread.start()
        # self.input_thread.start()  # Start input thread
        self.keyboard_handler.start()

        last_scan_time = 0
        last_layout_time = 0

        try:
            with Live(self._generate_layout(), refresh_per_second=4, screen=True) as live:
                while self.running:
                    try:
                        current_time = time.time()

                        # Force layout refresh every 0.5 seconds
                        if current_time - last_layout_time > 0.5:
                            live.update(self._generate_layout())
                            last_layout_time = current_time

                        # Perform scan at interval
                        if current_time - last_scan_time > Config.SCAN_INTERVAL:
                            self._perform_scan()
                            last_scan_time = current_time
                            live.update(self._generate_layout())  # Immediate update after scan

                        # Update UI
                        # live.update(self._generate_layout())

                        # Small sleep to prevent CPU overload
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
        """Perform network scan and update devices - FIXED"""
        # Get authenticated MACs
        auth_macs = set(self.data_source.get_authenticated_macs())

        # Scan network
        devices_data = self.scanner.scan_arp()
        writer.write(f"DATA: \n{devices_data}")

        # Update devices with thread lock
        with self.devices_lock:
            current_macs = set()

            for ip, mac, state in devices_data:
                current_macs.add(mac)

                if mac in self.devices:
                    device = self.devices[mac]
                    device.ip = ip  # Update IP
                    device.update()
                else:
                    device = Device(ip, mac, mac in auth_macs, state)
                    device.hostname = self.scanner.get_hostname(ip)
                    device.vendor = self.scanner.get_vendor(mac)
                    self.devices[mac] = device

            # Remove stale devices (not seen in current scan)
            stale_macs = set(self.devices.keys()) - current_macs
            for mac in stale_macs:
                # Keep for a while in case of intermittent connections
                device = self.devices[mac]
                if (datetime.now() - device.last_seen).seconds > 300:  # 5 minutes
                    del self.devices[mac]
                else:
                    # Mark as stale but keep
                    device.ip = "[stale]"

        # Update interface stats with thread lock
        with self.interface_stats_lock:
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
            Layout(name="devices", ratio=4),  # 4 parts out of 6 = ~67%
            Layout(name="stats", ratio=2)  # 2 parts out of 6 = ~33%
        )

        # Devices table
        devices_table = self._generate_devices_table_with_selection()
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

    def _generate_devices_table_with_selection(self) -> Table:
        """Generate devices table - clean version with text-only selection"""
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

        with self.devices_lock:
            devices_copy = list(self.devices.values())

        # Sort devices
        def ip_sort_key(device):
            try:
                ip_part = device.ip
                if '[' in ip_part:
                    import re
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', ip_part)
                    if ip_match:
                        ip_part = ip_match.group(1)
                return tuple(map(int, ip_part.split('.')))
            except Exception:
                return (255, 255, 255, 255)

        sorted_devices = sorted(devices_copy, key=ip_sort_key)

        for idx, device in enumerate(sorted_devices, 1):
            is_selected = (idx - 1) == self.selected_index

            # Get device info
            state = device.state
            hostname = device.hostname or "Unknown"

            if not device.hostname or device.hostname == "Unknown":
                device.hostname = self.scanner.get_hostname(device.ip)
                hostname = device.hostname or "Unknown"

            vendor = device.vendor or "Unknown"
            if len(vendor) > 22:
                vendor = vendor[:19] + "..."

            seen_secs = (datetime.now() - device.last_seen).seconds
            if seen_secs < 60:
                seen = f"{seen_secs}s"
            elif seen_secs < 3600:
                seen = f"{seen_secs // 60}m"
            else:
                seen = f"{seen_secs // 3600}h"

            cursor = ""
            if is_selected:
                # Selected row - just use brighter/different text color
                # highlight_color = "cyan"
                cursor = "▶"

            '''
                # All text in highlight color (status loses its green/red)
                status_text = "✓ AUTH" if device.authenticated else "✗ BLOCKED"

                table.add_row(
                    f"{cursor}[{highlight_color}]{device.ip}[/]",
                    f"[{highlight_color}]{device.mac}[/]",
                    f"[{highlight_color}]{status_text}[/]",
                    f"[{highlight_color}]{state}[/]",
                    f"[{highlight_color}]{hostname}[/]",
                    f"[{highlight_color}]{vendor}[/]",
                    f"[{highlight_color}]{seen}[/]"
                )
            else:
            '''
            if device.authenticated:
                status_display = "[green]✓ AUTH[/green]"
            else:
                status_display = "[red]✗ BLOCKED[/red]"

            table.add_row(
                f"{cursor}{device.ip}",
                device.mac,
                status_display,
                state,
                hostname,
                vendor,
                seen
            )

        return table

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

        with self.devices_lock:
            devices_copy = list(self.devices.values())

        # Sort devices by IP
        sorted_devices = sorted(devices_copy, key=lambda d: socket.inet_aton(d.ip.split('/')[0]) if d.ip.replace('.', '').isdigit() else '255.255.255.255')

        for idx, device in enumerate(sorted_devices, 1):
            # Status with color
            if device.authenticated:
                status = "[green]✓ AUTH[/green]"
            else:
                status = "[red]✗ BLOCKED[/red]"

            state = device.state

            # Hostname
            if not device.hostname or device.hostname == "Unknown":
                device.hostname = self.scanner.get_hostname(device.ip)

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

            # Highlight stale devices
            ip_display = device.ip
            if "[stale]" in device.ip:
                ip_display = f"[dim]{device.ip}[/dim]"

            table.add_row(
                ip_display,  # device.ip,
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
