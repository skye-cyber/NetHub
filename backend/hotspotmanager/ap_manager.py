#!/usr/bin/env python3
"""
Custom Hotspot Manager for Linux
Supports both NetworkManager and systemd-networkd
"""
import subprocess
from pathlib import Path
from ap_utils.config import config_manager, ConfigManager


BASE_DIR = Path(__file__).resolve().parent


class ApManager:
    def __init__(self, use_psk=True):
        self.config = {}

    def __enter__(self):
        self.config = config_manager.get_config

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

    def get_available_wifi_ifaces(self):
        """Get list of available wireless wifi_ifaces"""
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
            wifi_ifaces = []
            for line in result.stdout.split('\n'):
                if 'wl' in line and 'state UP' in line:
                    ifname = line.split(':')[1].strip()
                    wifi_ifaces.append(ifname)
            return wifi_ifaces
        except Exception as e:
            print(f"Error getting wifi_ifaces: {e}")
            return []

    def setup_nmcli_hotspot(self):
        """Setup hotspot using NetworkManager"""
        try:
            # Create hotspot connection
            subprocess.run([
                'nmcli', 'con', 'add', 'type', 'wifi', 'ifname', self.config['wifi_iface'],
                'con-name', 'xap0', 'autoconnect', 'no', 'ssid', self.config['ssid']
            ], check=True)

            # Set hotspot mode
            subprocess.run([
                'nmcli', 'con', 'modify', 'xap0', '802-11-wireless.mode', 'ap'
            ], check=True)

            if self.config['use_psk']:
                # Set security
                subprocess.run([
                    'nmcli', 'con', 'modify', 'xap0', '802-11-wireless-security.key-mgmt', 'wpa-psk'
                ], check=True)

                subprocess.run([
                    'nmcli', 'con', 'modify', 'xap0', '802-11-wireless-security.psk', self.config['password']
                ], check=True)

            # Set IP configuration
            subprocess.run([
                'nmcli', 'con', 'modify', 'xap0', 'ipv4.method', 'shared'
            ], check=True)

            print("NetworkManager 'xap0' configured successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error setting up NetworkManager hotspot: {e}")
            return False

    def setup_systemd_hotspot(self):
        """Setup hotspot using systemd-networkd and hostapd"""
        try:
            # Stop NetworkManager on the wifi_iface
            subprocess.run(['systemctl', 'stop', 'NetworkManager'], check=True)

            # Create hostapd configuration
            host_conf = ConfigManager(config_manager.__bconfdir__ / 'hostapd.json')

            hostapd_conf = host_conf.__str__

            print("HOST CONF:", hostapd_conf)
            """
            wifi_iface={self.config['wifi_iface']}
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
            _network_conf = self.config

            network_conf = (
                "[Match]\n"
                f"Name={_network_conf['wifi_iface']}\n\n"

                "[Network]\n"
                f"Address={_network_conf['gateway']}/24\n"
                "DHCPServer=yes\n\n"

                "[DHCPServer]\n"
                "PoolOffset=10\n"
                "PoolSize=50\n"
                "EmitDNS=yes\n"
                "DNS=8.8.8.8"
            )

            print("NETFCONF:", network_conf)
            with open(f'/etc/systemd/network/10-{self.config["wifi_iface"]}.network', 'w') as f:
                f.write(network_conf)

            # Enable and start services
            subprocess.run(['systemctl', 'enable', '--now', 'systemd-networkd'], check=True)
            subprocess.run(['systemctl', 'unmask', 'hostapd'], check=True)
            subprocess.run(['systemctl', 'enable', '--now', 'hostapd'], check=True)

            print(f"systemd-networkd {'xap0'} configured successfully")
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
                subprocess.run(['nmcli', 'con', 'up', 'xap0'], check=True)
        else:
            success = self.setup_systemd_hotspot()

        if success:
            print("Hotspot started successfully!")
            self.show_status()
        return success

    def stop_hotspot(self):
        """Stop the hotspot"""
        print("Stopping xap0...")

        if self.config['mode'] == 'nmcli':
            subprocess.run(['nmcli', 'con', 'down', 'xap0'], check=False)
            subprocess.run(['nmcli', 'con', 'delete', 'xap0'], check=False)
        else:
            subprocess.run(['systemctl', 'stop', 'hostapd'], check=False)
            subprocess.run(['systemctl', 'stop', 'systemd-networkd'], check=False)
            subprocess.run(['systemctl', 'start', 'NetworkManager'], check=False)

        print("Hotspot stopped")

    def show_status(self):
        """Show hotspot status"""
        print("\n=== Hotspot Status ===")
        print(f"SSID: {self.config['ssid']}")
        print(f"Interface: {self.config['wifi_iface']}")
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

    def configure(self, ssid=None, password=None, wifi_iface=None, mode=None):
        """Configure hotspot settings"""
        if ssid:
            self.config['ssid'] = ssid
        if password:
            self.config['password'] = password
        if wifi_iface:
            self.config['wifi_iface'] = wifi_iface
        if mode and mode in ['nmcli', 'systemd']:
            self.config['mode'] = mode

        self.save_config()
        print("Configuration updated successfully")
