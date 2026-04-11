# cli/auth.py
import click
from rich.console import Console
from rich.panel import Panel
from typing import Optional
import asyncio
from captive_portal.core.firewall import firewall
from commsys import APManagerCommunicator
from shared import cli


# Global communicator instance
communicator = None

console = Console()


def get_communicator():
    """Get or create communicator instance"""
    global communicator
    if communicator is None:
        communicator = APManagerCommunicator(
            base_url="http://localhost:8001",
            api_token=None,  # Set from config
        )
    return communicator


@cli.group()
def auth():
    """Device authentication management"""
    pass


@auth.command("authenticate")
@click.option("--mac", type=str, required=True, help="Device MAC address")
@click.option("--hook", type=str, help="Webhook URL for callback")
@click.option("--api", is_flag=True, default=True, help="Use Django API (default)")
@click.option("--local", is_flag=True, help="Use local firewall only")
@click.pass_context
def authenticate(ctx, mac: str, hook: Optional[str], api: bool, local: bool):
    """Authenticate device (allow internet access)"""

    if api and not local:
        # Use Django API
        comm = get_communicator()

        async def do_auth():
            result = await comm.authenticate_device(mac, hook)
            if result.get("success"):
                console.print(
                    Panel(
                        f"[green]✓ Device {mac} authenticated via API[/green]",
                        title="Success",
                    )
                )
                return True
            else:
                console.print(
                    Panel(
                        f"[red]✗ Failed: {result.get('error', 'Unknown error')}[/red]",
                        title="Error",
                    )
                )
                return False

        success = asyncio.run(do_auth())
        return success

    else:
        # Local firewall only
        from captive_portal.core.firewall import firewall

        try:
            firewall.authenticate(mac)
            console.print(
                Panel(
                    f"[green]✓ Device {mac} authenticated locally[/green]",
                    title="Success",
                )
            )

            # Send webhook if provided
            if hook:
                import requests

                try:
                    requests.post(
                        hook,
                        json={
                            "mac": mac,
                            "status": "authenticated",
                            "source": "local_firewall",
                        },
                        timeout=5,
                    )
                except Exception:
                    console.print("[yellow]⚠ Webhook failed[/yellow]")

            return True

        except Exception as e:
            console.print(
                Panel(f"[red]✗ Error: {str(e)}[/red]", title="Error", expand=False)
            )
            return False


@auth.command("block")
@click.option("--mac", type=str, required=True, help="Device MAC address")
@click.option("--hook", type=str, help="Webhook URL for callback")
@click.option("--api", is_flag=True, default=True, help="Use Django API (default)")
@click.option("--local", is_flag=True, help="Use local firewall only")
@click.pass_context
def block(ctx, mac: str, hook: Optional[str], api: bool, local: bool):
    """Block device (remove internet access)"""

    if api and not local:
        # Use Django API
        comm = get_communicator()

        async def do_block():
            result = await comm.block_device(mac, hook)
            if result.get("success"):
                console.print(
                    Panel(
                        f"[green]✓ Device {mac} blocked via API[/green]",
                        title="Success",
                    )
                )
                return True
            else:
                console.print(
                    Panel(
                        f"[red]✗ Failed: {result.get('error', 'Unknown error')}[/red]",
                        title="Error",
                    )
                )
                return False

        success = asyncio.run(do_block())
        return success

    else:
        # Local firewall only
        from captive_portal.core.firewall import firewall

        try:
            firewall.deauthenticate(mac)
            console.print(
                Panel(f"[green]✓ Device {mac} blocked locally[/green]", title="Success")
            )

            # Send webhook if provided
            if hook:
                import requests

                try:
                    requests.post(
                        hook,
                        json={
                            "mac": mac,
                            "status": "blocked",
                            "source": "local_firewall",
                        },
                        timeout=5,
                    )
                except Exception:
                    console.print("[yellow]⚠ Webhook failed[/yellow]")

            return True

        except Exception as e:
            console.print(
                Panel(f"[red]✗ Error: {str(e)}[/red]", title="Error"), expand=False
            )
            return False


@auth.command("status")
@click.option("--mac", type=str, required=True, help="Device MAC address")
@click.option("--hook", type=str, help="Webhook URL for callback")
@click.option("--api", is_flag=True, default=True, help="Use Django API (default)")
@click.option("--local", is_flag=True, help="Use local firewall only")
@click.pass_context
def status(ctx, mac: str, hook: Optional[str], api: bool, local: bool):
    """Check device authentication status"""
    if api and not local:
        # Use Django API
        comm = get_communicator()

        async def do_status():
            result = await comm.get_device_status(mac, hook)
            authenticated = result.get("authenticated", False)

            status_text = "AUTHENTICATED" if authenticated else "NOT AUTHENTICATED"
            status_color = "green" if authenticated else "red"
            status_icon = "✓" if authenticated else "✗"

            console.print(
                Panel(
                    f"Device: [magenta] {mac}[/magenta]\nStatus: [{status_color}]{status_icon}  {status_text}[/{status_color}]",
                    expand=False,
                    title="[bold]Status[/bold]",
                )
            )

            return authenticated

        return asyncio.run(do_status())

    else:
        # Local firewall check
        authenticated = firewall.auth_status(mac)

        status_text = "AUTHENTICATED" if authenticated else "NOT AUTHENTICATED"
        status_color = "green" if authenticated else "red"
        status_icon = "✓" if authenticated else "✗"

        console.print(
            Panel(
                f"Device: [magenta] {mac}[/magenta]\nStatus: [{status_color}]{status_icon}  {status_text}[/{status_color}]",
                expand=False,
                title="[bold]Status[/bold]",
            )
        )

        # Send webhook if provided
        if hook:
            import requests

            try:
                requests.post(
                    hook,
                    json={
                        "mac": mac,
                        "authenticated": authenticated,
                        "source": "local_firewall",
                    },
                    timeout=5,
                )
            except:
                console.print("[yellow]⚠ Webhook failed[/yellow]")

        return authenticated


@auth.command("monitor")
@click.option("--hook", type=str, help="WebSocket endpoint for real-time updates")
@click.option("--interval", type=int, default=10, help="Update interval in seconds")
@click.pass_context
def monitor(ctx, hook: Optional[str], interval: int):
    """Start real-time monitoring with Django"""

    comm = get_communicator()

    # Register callbacks for device events
    def on_device_connected(data):
        console.print(f"[cyan]📱 Device connected: {data.get('mac')}[/cyan]")

    def on_device_authenticated(data):
        console.print(f"[green]🔓 Device authenticated: {data.get('mac')}[/green]")

    comm.register_callback("device_connected", on_device_connected)
    comm.register_callback("device_authenticated", on_device_authenticated)

    # Start monitoring
    comm.start_monitoring()

    console.print(
        Panel(
            "[green]✅ Real-time monitoring started[/green]\n"
            f"[dim]• WebSocket: {comm.ws_url}[/dim]\n"
            f"[dim]• API: {comm.base_url}[/dim]\n"
            "[yellow]Press Ctrl+C to stop[/yellow]",
            title="[bold]Monitoring[/bold]",
            expand=False,
        )
    )

    # Keep running
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        comm.stop_monitoring()
        console.print("[yellow]⏹️ Monitoring stopped[/yellow]")


__all__ = ["auth"]
