import subprocess
import re
import os
from pathlib import Path
import logging

BASE_DIR = Path(__file__).parent.parent.resolve()
logger = logging.getLogger("Captive-Helper")


def get_client_mac(ip_address):
    """Get MAC address from IP using ARP table"""
    try:
        # Try to get MAC from ARP table
        result = subprocess.run(
            ["arp", "-n", ip_address], capture_output=True, text=True, check=True
        )

        # Parse MAC address from ARP output
        mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", result.stdout)
        if mac_match:
            return mac_match.group().lower()

        # If not in ARP table, try to ping and check again
        subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip_address], capture_output=True, check=False
        )

        result = subprocess.run(
            ["arp", "-n", ip_address], capture_output=True, text=True, check=True
        )
        mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", result.stdout)

        return mac_match.group().lower() if mac_match else None

    except Exception as e:
        print(f"Error getting MAC address: {e}")
        return None


def authenticate_mac(mac_address):
    """Add MAC address to authenticated list"""
    try:
        auth_file = (BASE_DIR / "auth/authenticated_macs").as_posix()

        # Read existing MACs
        existing_macs = set()
        if os.path.exists(auth_file):
            with open(auth_file, "r") as f:
                existing_macs = set(line.strip() for line in f if line.strip())

        # Add new MAC
        if mac_address not in existing_macs:
            with open(auth_file, "a") as f:
                f.write(f"{mac_address}\n")
            return True
        return True  # Already authenticated

    except Exception as e:
        logger.error(e)
        print(f"Error authenticating MAC: {e}")
        return False


def get_connected_devices():
    """Get list of all connected devices in the captive network"""
    devices = []
    try:
        # Get ARP entries for the captive network
        result = subprocess.run(
            ["arp", "-a"], capture_output=True, text=True, check=True
        )

        for line in result.stdout.split("\n"):
            if "192.168.12." in line:
                # Parse line like: ? (192.168.12.100) at ab:cd:ef:12:34:56 [ether] on wlan0
                ip_match = re.search(r"\((192\.168\.12\.\d+)\)", line)
                mac_match = re.search(r"at\s+([0-9A-Fa-f:]{17})", line)
                interface_match = re.search(r"on\s+(\w+)", line)

                if ip_match and mac_match:
                    devices.append(
                        {
                            "ip": ip_match.group(1),
                            "mac": mac_match.group(1).lower(),
                            "interface": interface_match.group(1)
                            if interface_match
                            else "unknown",
                            "authenticated": is_mac_authenticated(
                                mac_match.group(1).lower()
                            ),
                        }
                    )

    except Exception as e:
        print(f"Error getting connected devices: {e}")

    return devices


def is_mac_authenticated(mac_address):
    """Check if MAC address is authenticated"""
    auth_file = BASE_DIR / "auth/authenticated_macs"
    if os.path.exists(auth_file):
        with open(auth_file, "r") as f:
            authenticated_macs = set(line.strip() for line in f if line.strip())
        return mac_address in authenticated_macs
    return False
