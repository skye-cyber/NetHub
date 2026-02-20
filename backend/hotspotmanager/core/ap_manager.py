#!/usr/bin/env python3
"""
Custom Hotspot Manager for Linux
Supports both NetworkManager and systemd-networkd
"""
import os
import sys
from typing import Optional, List
import subprocess
from pathlib import Path
from ap_utils.config import config_manager, ConfigManager
from core.lock import lock
from core.netmanager import NetworkManager
from core.cleanup import CleanupManager
from core.interface_manager import InterfaceManager
from core.network_config import NetworkConfigurator
from core.process_manager import ProcessManager
from ap_utils.colors import fg
from ap_utils.command import command
from ap_utils.resource import increase_resource_limits


BASE_DIR = Path(__file__).resolve().parent

# Check if we're running as root
if os.geteuid() != 0:
    print("This script must be run as root")
    sys.exit(1)


class ApManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __enter__(self):
        self.config = config_manager.get_config
        self.clean = CleanupManager(self)
        command.set_cleanup_manager(self.clean)

    @classmethod
    def get_instance(cls):
        return cls()

    def __init__(self):
        self.config_manager = config_manager

        self.config = config_manager.get_config
        # make sure that all command outputs are in english
        # so we can parse them correctly
        # subprocess.run(['export', 'LC_ALL=C'])

        # all new files and directories must be readable only by root.
        # in special cases we must use chmod to give any other permissions.
        # self.SCRIPT_UMASK = "0077"

        # lock file for the mutex counter
        self.COUNTER_LOCK_FILE = f"/tmp/ap_manager.{os.getpid()}.lock"

        # Lock file descriptor
        self.lock_fd = None

        self.use_iwconfig = False
        # lock manager
        self.lock = lock
        self.netmanager = NetworkManager(self)

        self.networkmanager_conf = "/etc/NetworkManager/NetworkManager.conf"
        self.nm_older_version = 1

        self.clean = CleanupManager(self)

        # Initialize new manager modules
        self.interface_manager = InterfaceManager(self)
        self.network_config = NetworkConfigurator(self)
        self.process_manager = ProcessManager(self)

        self.proc_dir = self.config['proc_dir']
        self.conf_dir = self.config.get('conf_dir', config_manager.__bconfdir__)

        os.makedirs(self.proc_dir, exist_ok=True)
        os.makedirs(self.conf_dir, exist_ok=True)

        # Set proper permissions for base_dir
        # os.chmod(self.config['base_dir'], 0o444)

        self.iface_dir = os.path.join(self.config['base_dir'], 'ifaces')

        self.virt_diems = "Maybe your WiFi adapter does not fully support virtual interfaces. Try again with --no-virt."

        # Increase resource limits to prevent file descriptor issues
        increase_resource_limits()

    def setup_accesspoint(self):
        """Initialize the access point with proper configuration."""
        try:
            # Use the new interface manager to initialize the access point
            self.interface_manager.initialize_access_point()

            # Print configuration information
            if self.config['hidden']:
                print("Access Point's SSID is hidden!")
            if self.config['mac_filter']:
                print("MAC address filtering is enabled!")
            if self.config['isolate_clients']:
                print("Access Point's clients will be isolated!")

            # Configure services
            try:
                self.interface_manager.initialize_wifi_interface()
            except Exception as e:
                self.clean.die(f"Failed to configure services: {str(e)}")

            # Exit cleanly
            print("Success")
            # self.clean.clean_exit("Success")
            return True

        except Exception as e:
            self.clean.die(f"Initialization failed: {str(e)}")

    def start_ap(self):
        print(f"{fg.YELLOW}hostapd{fg.RESET} command-line interface: {fg.LYELLOW}hostapd_cli -p {self.conf_dir}/hostapd_ctrl{fg.RESET}")
        if self.config['no_haveged']:
            self.haveged_watchdog()
            # HAVEGED_WATCHDOG_PID =

    # Method moved to InterfaceManager
    def make_unmanaged(self):
        self.interface_manager.make_interface_unmanaged()

    # Method moved to InterfaceManager
    def iface_freq_channel_setup(self):
        self.interface_manager.setup_frequency_and_channel()

    # Method moved to InterfaceManager
    def create_virt_iface(self):
        self.interface_manager.create_virtual_interface()

    # Method moved to InterfaceManager
    def _get_channels_(self) -> bool:
        return self.interface_manager._get_channels_()

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

    def get_all_available_ifaces(self):
        """Get list of available wireless wifi_ifaces"""
        try:
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
            wifi_ifaces = []
            for line in result.stdout.split('\n'):
                state = "UP" if "state UP" in line else 'DOWN'

                # if 'wl' in line and 'state UP' in line:
                if len(line.split(':')) < 2 or not any([state_str in line for state_str in ('state UP', 'state DOWN')]):
                    continue

                ifname = line.split(':')[1].strip()
                ifype_map = {
                    'eth' in ifname: "ethernet",
                    'wlan' in ifname: "wireless",
                    'br' in ifname: "bridge",
                    'ap' in ifname: "access point"
                }
                itype = 'ethernet' if 'eth' in ifname else 'wireless' if 'wlan' in ifname else 'bridge' if 'br' in ifname else 'access point' if 'ap' in ifname else '-'

                wifi_ifaces.append({"name": ifname, "state": state, "type": itype})
            return wifi_ifaces
        except Exception as e:
            print(f"Error getting wifi_ifaces: {e}")
            return []

    def setup_nmcli_hotspot(self):
        """Setup hotspot using NetworkManager"""
        try:
            return self._ap_init_()

            # Create hotspot connection
            subprocess.run([
                'nmcli', 'con', 'add', 'type', 'wifi', 'ifname', self.config['wifi_iface'],
                'con-name', self.config['vwifi_iface'], 'autoconnect', 'no', 'ssid', self.config['ssid']
            ], check=True)

            # Set hotspot mode
            subprocess.run([
                'nmcli', 'con', 'modify', self.config['vwifi_iface'], '802-11-wireless.mode', 'ap'
            ], check=True)

            if self.config['use_psk']:
                # Set security
                subprocess.run([
                    'nmcli', 'con', 'modify', self.config['vwifi_iface'], '802-11-wireless-security.key-mgmt', 'wpa-psk'
                ], check=True)

                subprocess.run([
                    'nmcli', 'con', 'modify', self.config['vwifi_iface'], '802-11-wireless-security.psk', self.config['password']
                ], check=True)

            # Set IP configuration
            subprocess.run([
                'nmcli', 'con', 'modify', 'xap0', 'ipv4.method', 'shared'
            ], check=True)

            print(f"NetworkManager '{self.config['vwifi_iface']}' configured successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error setting up NetworkManager hotspot: {e}")
            return False

    def setup_systemd_hotspot(self):
        """Setup hotspot using systemd-networkd and hostapd"""
        try:
            return self._ap_init_()
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

    def start_nmcli_hotspot(self):
        """Start the hotspot"""
        if not self.check_dependencies():
            return False

        print(f"Starting hotspot with SSID: {self.config['ssid']}")

        return self._ap_init_()

        if self.config['mode'] == 'nmcli':
            success = self.setup_nmcli_hotspot()
            if success:
                subprocess.run(['nmcli', 'con', 'up', self.config['vwifi_iface']], check=True)
        else:
            success = self.setup_systemd_hotspot()

        if success:
            print("Hotspot started successfully!")
            self.show_status()
        return success

    def stop_nmcli_hotspot(self):

        try:
            if self.config['mode'] == 'nmcli':
                # Use NetworkManager CLI for stopping and deleting the connection
                command.run(['nmcli', 'con', 'down', self.config['vwifi_iface']],
                            check=True, capture_output=True)
                command.run(['nmcli', 'con', 'delete', self.config['vwifi_iface']],
                            check=True, capture_output=True)
            else:
                # Stop hostapd service
                command.run(['systemctl', 'stop', 'hostapd'],
                            check=True, capture_output=True)

                # Stop systemd-networkd service
                command.run(['systemctl', 'stop', 'systemd-networkd'],
                            check=True, capture_output=True)

                # Restart NetworkManager
                command.run(['systemctl', 'start', 'NetworkManager'],
                            check=True, capture_output=True)

                # Additional cleanup using iw and ip commands
                self._cleanup_network_interface()

            print("Hotspot stopped successfully")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to stop hotspot completely: {str(e)}")
            # Continue with cleanup even if some commands fail

    def _cleanup_network_interface(self):
        """Perform additional cleanup using iw and ip commands."""
        try:
            # Bring down the interface
            command.run(['ip', 'link', 'set', 'dev', self.config['vwifi_iface'], 'down'],
                        check=True, capture_output=True)

            # Flush IP addresses
            command.run(['ip', 'addr', 'flush', self.config['vwifi_iface']],
                        check=True, capture_output=True)

            # Remove the interface if it's a virtual interface
            if not self.config.get('no_virt', False):
                command.run(['iw', 'dev', self.config['vwifi_iface'], 'del'],
                            check=True, capture_output=True)

            # Remove from NetworkManager unmanaged list if needed
            if self.netmanager.networkmanager_is_running():
                self.netmanager.networkmanager_rm_unmanaged_if_needed(
                    self.config['vwifi_iface'],
                    self.config.get('old_macaddr')
                )

        except subprocess.CalledProcessError as e:
            print(f"Warning: Network cleanup failed: {str(e)}")

    def show_status(self):
        """Show hotspot status"""
        print(f"\n{fg.BWHITE}{fg.LWHITE}Hotspot Status{fg.RESET}")
        print(f"SSID: {self.config['ssid']}")
        print(f"Wifi Interface: {self.config['wifi_iface']}")
        print(f"Virtual Interface: {self.config['vwifi_iface']}")
        print(f"Connected to: {self.config['internet_iface']}")
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

    def configure(self, args: dict = {}):
        """Configure hotspot settings"""
        self.config_manager._dict_update(None, args)
        self.config_manager.save_config()
        print("Configuration updated successfully")

    # taken from iw/util.c
    def ieee80211_frequency_to_channel(self, _freq=None):
        _freq = _freq if _freq else self.config['freq_band']

        """Convert frequency to channel number (taken from iw/util.c)"""
        freq = int(_freq.split('.')[0])

        if freq < 1000:
            return 0
        elif freq == 2484:
            return 14
        elif freq == 5935:
            return 2
        elif freq < 2484:
            return (freq - 2407) // 5
        elif 4910 <= freq <= 4980:
            return (freq - 4000) // 5
        elif freq < 5950:
            return (freq - 5000) // 5
        elif freq <= 45000:
            return (freq - 5950) // 5
        elif 58320 <= freq <= 70200:
            return (freq - 56160) // 2160
        else:
            return 0

    def stop_accesspoint(self):
        """Stop the hotspot using appropriate network management tools."""
        self.interface_manager.stop_accesspoint()
        print(f"Stopping {self.config['vwifi_iface']}...")
        return self.clean.clean_exit("Stopping ap manager...")

    # Methods moved to InterfaceManager
    def is_5ghz_frequency(self, freq=None):
        return self.interface_manager.is_5ghz_frequency(freq)

    def is_wifi_connected(self, iface=None):
        return self.interface_manager.is_wifi_connected(iface)

    def is_macaddr(self, mac=None):
        return self.interface_manager.is_mac_address(mac)

    def is_unicast_macaddr(self, mac=None):
        return self.interface_manager.is_unicast_mac_address(mac)

    def is_interface(self, iface=None):
        return self.interface_manager.is_interface(iface)

    def get_macaddr(self, iface=None):
        return self.interface_manager.get_mac_address(iface)

    def get_mtu(self, iface=None) -> int:
        return self.interface_manager.get_mtu(iface)

    def alloc_new_iface(self, prefix=None):
        return self.interface_manager.alloc_new_iface(prefix)

    def dalloc_iface(self, iface=None):
        return self.interface_manager.dealloc_iface(iface)

    @property
    def has_hostapd(self):
        return subprocess.run(['which', 'hostapd'], check=True, capture_output=True).returncode == 0

    @property
    def where_hostapd(self):
        return subprocess.run(['which', 'hostapd'], check=True, capture_output=True, text=True).stdout

    # Methods moved to InterfaceManager
    def can_transmit_to_channel(self, iface=None, channel=None):
        return self.interface_manager.can_transmit_to_channel(iface, channel)

    def can_be_ap(self, iface=None):
        return self.interface_manager.can_be_ap(iface)

    def can_be_sta_and_ap(self, iface=None):
        return self.interface_manager.can_be_sta_and_ap(iface)

    def get_adapter_kernel_module(self, _iface=None) -> str:
        return self.interface_manager.get_adapter_kernel_module(_iface)

    def get_adapter_info(self, iface=None) -> str:
        return self.interface_manager.get_adapter_info(iface)

    def get_phy_device(self, iface=None) -> str:
        return self.interface_manager.get_phy_device(iface)

    def is_bridge_interface(self, _iface=None):
        return self.interface_manager.is_bridge_interface(_iface)

    def is_wifi_interface(self, _iface=None):
        return self.interface_manager.is_wifi_interface(_iface)

    @property
    def get_all_macaddrs(self) -> list:
        return self.interface_manager.get_all_mac_addresses

    def get_new_macaddr(self, iface=None):
        return self.interface_manager.get_new_mac_address(iface)

    # Methods moved to ProcessManager
    def haveged_watchdog(self):
        self.process_manager.start_haveged_watchdog()

    def is_haveged_installed(self):
        return self.process_manager.is_haveged_installed()

    def is_haveged_running(self):
        return self.process_manager.is_haveged_running()

    def start_haveged_watchdog(self):
        return self.process_manager.start_haveged_watchdog()

    # Methods moved to ProcessManager
    def get_wifi_iface_from_pid(self, pid: str) -> Optional[str]:
        return self.process_manager.get_wifi_iface_from_pid(pid)

    def get_pid_from_wifi_iface(self, wifi_iface: str) -> Optional[str]:
        return self.process_manager.get_pid_from_wifi_iface(wifi_iface)

    def get_confdir_from_pid(self, pid: str) -> Optional[str]:
        return self.process_manager.get_confdir_from_pid(pid)

    def print_client(self, mac: str) -> None:
        self.process_manager.print_client(mac)

    def list_clients(self, pid_or_iface: str) -> None:
        self.process_manager.list_clients(pid_or_iface)

    # Methods moved to ProcessManager
    def has_running_instance(self) -> bool:
        return self.process_manager.has_running_instance()

    def is_running_pid(self, pid: str) -> bool:
        return self.process_manager.is_running_pid(pid)

    def list_running_conf(self) -> List[str]:
        return self.process_manager.list_running_conf()

    def list_running(self) -> List[str]:
        return self.process_manager.list_running()

    def send_stop(self, pid_or_iface: str) -> None:
        self.process_manager.send_stop_signal(pid_or_iface)
