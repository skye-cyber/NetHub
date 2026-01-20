import subprocess
import re
from pathlib import Path
from typing import List, Callable, Optional


class Firewall:
    def __init__(self):
        self.client_interface = 'xap0'
        self.internet_interface = 'eth0'
        self.BASE_DIR = '/etc/ap_manager'
        self.gateway_address = "192.168.100.1"
        self.subnet = "192.168.100.0/24"
        self.captive_port = '8888'
        self.AUTH_DIR = Path(self.BASE_DIR) / 'auth'
        self.mac_file = self.AUTH_DIR / 'authenticated_macs'

    def get_existing(self) -> int:
        """Get count of existing MAC rules in CAPTIVE_PORTAL chain"""
        try:
            result = subprocess.run(
                ["iptables", "-L", "CAPTIVE_PORTAL", "-n"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            existing_mac_count = len([line for line in result.stdout.split('\n')
                                      if re.search(r'^[0-9a-f]{2}(?:[/-][0-9a-f]{2}){5}$', line, re.IGNORECASE)])
            print(f"Found {existing_mac_count} existing MAC rules in CAPTIVE_PORTAL chain")
            return existing_mac_count
        except Exception:
            return 0

    def update(self, macs: List[str]) -> bool:
        """Update firewall rules for given MAC addresses"""
        self.process_macs(macs=macs, callback=self.flush_contrac)
        print("Firewall rules updated")
        return True

    def verify_chains(self):
        """Verify and display current iptables chains"""
        print("CAPTIVE_PORTAL chain:")
        subprocess.run(["iptables", "-L", "CAPTIVE_PORTAL", "-n", "--line-numbers"], check=True)

        print("\nAUTH_REDIRECT chain:")
        subprocess.run(["iptables", "-t", "nat", "-L", "AUTH_REDIRECT", "-n", "--line-numbers"], check=True)

    def process_macs(self, macs: Optional[List[str]], callback: Optional[Callable[[str], bool]] = None):
        """Process MAC addresses and apply callback if provided"""
        if not macs:
            return

        for mac in macs:
            mac = mac.strip()
            if not mac:
                continue

            cleaned_mac = self.clean_mac(mac)
            if not self.validate_mac(cleaned_mac):
                print(f"Invalid MAC format: {mac}")
                continue

            print(f"Processing MAC: {cleaned_mac}")
            if callback:
                callback(cleaned_mac)
            else:
                self.update_firewall(cleaned_mac)

    def clean_mac(self, mac: str) -> str:
        """Clean and standardize MAC address format"""
        return re.sub(r'[^0-9a-fA-F]', '', mac).lower()

    def validate_mac(self, mac: str) -> bool:
        """Validate MAC address format"""
        return bool(re.fullmatch(r'^([0-9a-f]{2}:){5}[0-9a-f]{2}$', mac, re.IGNORECASE))

    def update_firewall(self, mac: str):
        """Update iptables rules for given MAC address"""
        # Check if MAC rule already exists in CAPTIVE_PORTAL
        check_cmd = ["iptables", "-C", "CAPTIVE_PORTAL", "-m", "mac", "--mac-source", mac]
        if subprocess.run(check_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
            print(f"Adding internet access for MAC: {mac}")
            subprocess.run(["iptables", "-I", "CAPTIVE_PORTAL", "1", "-m", "mac", "--mac-source", mac, "-j", "ACCEPT"])
        else:
            print(f"MAC {mac} already has access")

        # Check if MAC rule already exists in AUTH_REDIRECT
        check_cmd = ["iptables", "-t", "nat", "-C", "AUTH_REDIRECT", "-m", "mac", "--mac-source", mac]
        if subprocess.run(check_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
            print(f"Adding redirect exemption for MAC: {mac}")
            subprocess.run(["iptables", "-t", "nat", "-I", "AUTH_REDIRECT", "1", "-m", "mac", "--mac-source", mac, "-j", "RETURN"])
        else:
            print(f"MAC {mac} already has redirect exemption")

    def list_from_file(self, file: str) -> List[str]:
        """Read MAC addresses from file"""
        try:
            with open(file, 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            return []

    def flush_contrac(self, mac: str) -> bool:
        """Flush connection tracking for given MAC address"""
        print(f"Flushing connection tracking for MAC: {mac}")
        subprocess.run(["conntrack", "-D", "-m", mac], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True


# Initialize firewall instance
firewall = Firewall()
