#!/usr/bin/env python3
"""
Network Device Scanning and monitoring
"""
import re
import socket
import subprocess
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from .config import Config
from .writer import writer


# ==================== Network Scanner ====================

class NetworkScanner:
    """Scans network for connected devices"""

    def __init__(self, interface: str, subnet: str):
        self.interface = interface
        self.subnet = subnet
        self.oui_db = self._load_oui_database()

    def _load_oui_database(self) -> Dict[str, str]:
        """Load OUI database for vendor lookup"""
        oui_file = Path("/usr/share/ieee-data/oui.txt")
        oui_db = {}

        if oui_file.exists():
            try:
                with open(oui_file, 'r') as f:
                    for line in f:
                        if "(hex)" in line:
                            parts = line.split("(hex)")
                            if len(parts) == 2:
                                oui = parts[0].strip().replace('-', ':').lower()
                                vendor = parts[1].strip()
                                oui_db[oui] = vendor
            except Exception:
                pass

        return oui_db

    def scan_arp(self) -> List[Tuple[str, str]]:
        """Scan ARP table for devices on the interface"""
        devices = []

        try:
            # Get ARP entries for the interface
            cmd = ["ip", "neigh", "show", "dev", self.interface]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            states = ["REACHABLE", "FAILED", "STALE"]

            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 4:
                        ip = parts[0]
                        mac = parts[2].lower()
                        if self._is_valid_mac(mac) and self.is_valid_ip(ip):
                            seen_states = [state for state in states if state in parts]

                            device_state = seen_states[0] if len(seen_states) > 0 else '-'

                            devices.append((ip, mac, device_state))

        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print(f"ARP scan error: {e}")

        return devices

    def get_hostname(self, ip: str) -> Optional[str]:
        """Get hostname via reverse DNS lookup"""
        try:
            # Try local DNS first
            result = subprocess.run(
                ["nslookup", ip, Config.DNS_SERVER],
                capture_output=True, text=True, timeout=2
            )

            for line in result.stdout.split('\n'):
                if "name =" in line:
                    hostname = line.split('=')[1].strip().rstrip('.')
                    return hostname

            # Fallback to socket
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except Exception:
            return None

    def get_vendor(self, mac: str) -> Optional[str]:
        """Get vendor from OUI database"""
        if not self.oui_db:
            return None

        # Extract OUI (first 6 chars of MAC)
        oui = ':'.join(mac.split(':')[:3]).lower()
        return self.oui_db.get(oui, None)

    def get_connection_info(self, mac: str) -> Dict:
        """Get connection info from iptables/connection tracking"""
        info = {'rx_bytes': 0, 'tx_bytes': 0, 'connections': 0}

        try:
            # Get connection count
            cmd = ["conntrack", "-L", "-d", self.subnet.split('/')[0]]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)

            for line in result.stdout.split('\n'):
                if mac.replace(':', '').lower() in line.lower():
                    info['connections'] += 1

            # Get traffic stats (simplified - would need more sophisticated tracking)
            # This is a placeholder for actual traffic monitoring

        except Exception:
            pass

        return info

    def is_valid_ip(self, ip: str) -> bool:
        ip_match = re.search(r'[0-9]+[\.0-9]*', ip).group(0)
        return ip_match and len(ip_match.split('.')) >= 4

    def _is_valid_mac(self, mac: str) -> bool:
        """Validate MAC address format"""
        mac_pattern = re.compile(r'^([0-9a-f]{2}[:-]){5}([0-9a-f]{2})$', re.IGNORECASE)
        return bool(mac_pattern.match(mac))

    def get_interface_stats(self) -> Dict:
        """Get interface statistics"""
        stats = {'rx_bytes': 0, 'tx_bytes': 0, 'rx_packets': 0, 'tx_packets': 0}

        try:
            cmd = ["ip", "-s", "link", "show", self.interface]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)

            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if "RX:" in line and i + 1 < len(lines):
                    rx_line = lines[i + 1]
                    parts = rx_line.strip().split()
                    if len(parts) >= 2:
                        stats['rx_bytes'] = int(parts[0])
                        stats['rx_packets'] = int(parts[1])

                if "TX:" in line and i + 1 < len(lines):
                    tx_line = lines[i + 1]
                    parts = tx_line.strip().split()
                    if len(parts) >= 2:
                        stats['tx_bytes'] = int(parts[0])
                        stats['tx_packets'] = int(parts[1])

        except Exception:
            pass

        return stats
