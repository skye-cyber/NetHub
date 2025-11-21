#!/usr/bin/env python3
"""
Custom Hotspot Manager for Linux
Supports both NetworkManager and systemd-networkd
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path

class HotspotManager:
    def __init__(self):
        self.config_file = Path.home() / '.hotspot_config.json'
        self.default_config = {
            'ssid': 'MyCustomHotspot',
            'password': 'StrongPassword123',
            'interface': 'wlan0',
            'mode': 'nmcli',  # 'nmcli' or 'systemd'
            'channel': '6',
            'ip_range': '192.168.100.0/24',
            'gateway': '192.168.100.1'
        }
        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)
                self.config = {**self.default_config, **user_config}
        else:
            self.config = self.default_config
            self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def check_dependencies(self):
        """Check if required tools are available"""
        required_tools = ['iptables', 'dnsmasq']
        if self.config['mode'] == 'nmcli':
            required_tools.append('nmcli')
        else:
            required_tools.extend(['systemctl', 'hostapd'])

        missing_tools = []
        for tool in required_tools:
            if subprocess.call(['which', tool], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
                missing_tools.append(tool)

        if missing_tools:
            print(f"Missing required tools: {', '.join(missing_tools)}")
            return False
        return True

    def get_available_interfaces(self):
        """Get list of available wireless interfaces"""
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
            interfaces = []
            for line in result.stdout.split('\n'):
                if 'wl' in line and 'state UP' in line:
                    ifname = line.split(':')[1].strip()
                    interfaces.append(ifname)
            return interfaces
        except Exception as e:
            print(f"Error getting interfaces: {e}")
            return []

    def setup_nmcli_hotspot(self):
        """Setup hotspot using NetworkManager"""
        try:
            # Create hotspot connection
            subprocess.run([
                'nmcli', 'con', 'add', 'type', 'wifi', 'ifname', self.config['interface'],
                'con-name', 'hotspot', 'autoconnect', 'no', 'ssid', self.config['ssid']
            ], check=True)

            # Set hotspot mode
            subprocess.run([
                'nmcli', 'con', 'modify', 'hotspot', '802-11-wireless.mode', 'ap'
            ], check=True)

            # Set security
            subprocess.run([
                'nmcli', 'con', 'modify', 'hotspot', '802-11-wireless-security.key-mgmt', 'wpa-psk'
            ], check=True)

            subprocess.run([
                'nmcli', 'con', 'modify', 'hotspot', '802-11-wireless-security.psk', self.config['password']
            ], check=True)

            # Set IP configuration
            subprocess.run([
                'nmcli', 'con', 'modify', 'hotspot', 'ipv4.method', 'shared'
            ], check=True)

            print("NetworkManager hotspot configured successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error setting up NetworkManager hotspot: {e}")
            return False

    def setup_systemd_hotspot(self):
        """Setup hotspot using systemd-networkd and hostapd"""
        try:
            # Stop NetworkManager on the interface
            subprocess.run(['systemctl', 'stop', 'NetworkManager'], check=True)

            # Create hostapd configuration
            hostapd_conf = f"""
interface={self.config['interface']}
driver=nl80211
ssid={self.config['ssid']}
hw_mode=g
channel={self.config['channel']}
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={self.config['password']}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""

            with open('/etc/hostapd/hostapd.conf', 'w') as f:
                f.write(hostapd_conf)

            # Create systemd network configuration
            network_conf = f"""
[Match]
Name={self.config['interface']}

[Network]
Address={self.config['gateway']}/24
DHCPServer=yes

[DHCPServer]
PoolOffset=10
PoolSize=50
EmitDNS=yes
DNS=8.8.8.8
"""

            with open(f'/etc/systemd/network/10-{self.config["interface"]}.network', 'w') as f:
                f.write(network_conf)

            # Enable and start services
            subprocess.run(['systemctl', 'enable', '--now', 'systemd-networkd'], check=True)
            subprocess.run(['systemctl', 'enable', '--now', 'hostapd'], check=True)

            print("systemd-networkd hotspot configured successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error setting up systemd hotspot: {e}")
            return False

    def start_hotspot(self):
        """Start the hotspot"""
        if not self.check_dependencies():
            return False

        print(f"Starting hotspot with SSID: {self.config['ssid']}")

        if self.config['mode'] == 'nmcli':
            success = self.setup_nmcli_hotspot()
            if success:
                subprocess.run(['nmcli', 'con', 'up', 'hotspot'], check=True)
        else:
            success = self.setup_systemd_hotspot()

        if success:
            print("Hotspot started successfully!")
            self.show_status()
        return success

    def stop_hotspot(self):
        """Stop the hotspot"""
        print("Stopping hotspot...")

        if self.config['mode'] == 'nmcli':
            subprocess.run(['nmcli', 'con', 'down', 'hotspot'], check=False)
            subprocess.run(['nmcli', 'con', 'delete', 'hotspot'], check=False)
        else:
            subprocess.run(['systemctl', 'stop', 'hostapd'], check=False)
            subprocess.run(['systemctl', 'stop', 'systemd-networkd'], check=False)
            subprocess.run(['systemctl', 'start', 'NetworkManager'], check=False)

        print("Hotspot stopped")

    def show_status(self):
        """Show hotspot status"""
        print("\n=== Hotspot Status ===")
        print(f"SSID: {self.config['ssid']}")
        print(f"Interface: {self.config['interface']}")
        print(f"Mode: {self.config['mode']}")
        print(f"Gateway: {self.config['gateway']}")

        if self.config['mode'] == 'nmcli':
            result = subprocess.run(['nmcli', 'con', 'show', '--active'], capture_output=True, text=True)
            if 'hotspot' in result.stdout:
                print("Status: ACTIVE")
            else:
                print("Status: INACTIVE")
        else:
            result = subprocess.run(['systemctl', 'is-active', 'hostapd'], capture_output=True, text=True)
            print(f"hostapd Status: {result.stdout.strip()}")

    def configure(self, ssid=None, password=None, interface=None, mode=None):
        """Configure hotspot settings"""
        if ssid:
            self.config['ssid'] = ssid
        if password:
            self.config['password'] = password
        if interface:
            self.config['interface'] = interface
        if mode and mode in ['nmcli', 'systemd']:
            self.config['mode'] = mode

        self.save_config()
        print("Configuration updated successfully")

def main():
    parser = argparse.ArgumentParser(description='Custom Hotspot Manager')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'configure', 'interfaces'],
                       help='Action to perform')
    parser.add_argument('--ssid', help='SSID for the hotspot')
    parser.add_argument('--password', help='Password for the hotspot')
    parser.add_argument('--interface', help='Wireless interface to use')
    parser.add_argument('--mode', choices=['nmcli', 'systemd'], help='Hotspot mode')

    args = parser.parse_args()
    manager = HotspotManager()

    if args.action == 'start':
        manager.start_hotspot()
    elif args.action == 'stop':
        manager.stop_hotspot()
    elif args.action == 'status':
        manager.show_status()
    elif args.action == 'configure':
        manager.configure(args.ssid, args.password, args.interface, args.mode)
    elif args.action == 'interfaces':
        interfaces = manager.get_available_interfaces()
        print("Available wireless interfaces:")
        for iface in interfaces:
            print(f"  - {iface}")

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("This script must be run as root")
        sys.exit(1)
    main()
