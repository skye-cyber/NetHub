#!/usr/bin/env python3
"""
Custom Hotspot Manager for Linux
Supports both NetworkManager and systemd-networkd
"""
import re
import os
import shutil
import sys
import time
from threading import Thread
import subprocess
from pathlib import Path
from ap_utils.config import config_manager, ConfigManager
from lock import lock
from netmanager import NetworkManager
from cleanup import CleanupManager
import tempfile
from ap_utils.copy import cp_n_safe

BASE_DIR = Path(__file__).resolve().parent


class ApManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls()

    def __init__(self, use_psk=True):
        self.config_manager = config_manager

        self.config = {}
        # make sure that all command outputs are in english
        # so we can parse them correctly
        # subprocess.run(['export', 'LC_ALL=C'])

        # all new files and directories must be readable only by root.
        # in special cases we must use chmod to give any other permissions.
        self.SCRIPT_UMASK = "0077"

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

        self.proc_dir = self.config['proc_dir']
        self.conf_dir = self.config['proc_dir']
        self.iface_dir = os.path.join(self.config['base_dir'], 'ifaces')
        self.virt_diems = "Maybe your WiFi adapter does not fully support virtual interfaces. Try again with --no-virt."

    def __enter__(self):
        self.config = config_manager.get_config

    def _ap_init_(self):
        """Initialize the access point with proper configuration."""
        try:
            # Lock mutex for thread safety
            self.lock.mutex_lock()

            conf_dir = self.config['proc_dir']

            # Create configuration directory if it doesn't exist
            os.makedirs(self.config['common_conf_dir'], exist_ok=True)

            # Write PID file
            pid_file = os.path.join(conf_dir, 'pid')
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))

            # Set proper permissions for the PID file
            os.chmod(pid_file, 0o444)

            # Write internet interface information
            nat_internet_file = os.path.join(conf_dir, 'nat_internet_iface')
            with open(nat_internet_file, 'w') as f:
                f.write(self.config['internet_iface'])

            forwarding_src = f"/proc/sys/net/ipv4/conf/{self.config['internet_iface']}/forwarding"
            forwarding_dst = os.path.join(conf_dir, f"{self.config['internet_iface']}_forwarding")
            cp_n_safe(forwarding_src, forwarding_dst)

            ip_forward_src = "/proc/sys/net/ipv4/ip_forward"
            ip_forward_dst = os.path.join(conf_dir, 'ip_forward')
            cp_n_safe(ip_forward_src, ip_forward_dst)

            if os.path.exists('/proc/sys/net/bridge/bridge-nf-call-iptables'):
                bridge_src = '/proc/sys/net/bridge/bridge-nf-call-iptables'
                bridge_dst = os.path.join(conf_dir, 'bridge-nf-call-iptables')
            cp_n_safe(bridge_src, bridge_dst)

            # Unlock mutex
            self.lock.mutex_unlock()

            # Determine bridge interface
            if self.config['share_method'] == "bridge":
                if self.is_bridge_interface(self.config['internet_iface']):
                    self.config['bridge_iface'] = self.config['internet_iface']
                else:
                    self.config['bridge_iface'] = self.alloc_new_iface('xbr')

            # Disable power save mode if using iwconfig
            if self.use_iwconfig:
                try:
                    subprocess.run(
                        ['iw', 'dev', self.config['wifi_iface'], 'set', 'power_save', 'off'],
                        check=True
                    )
                except subprocess.CalledProcessError as e:
                    self.clean.die(f"Failed to set power save mode: {str(e)}")

            # Setup frequency and channel
            self.iface_freq_channel_setup()

            # Create virtual interface if needed
            if self.config['no_virt']:
                self.config['vwifi_iface'] = self.alloc_new_iface('xap')

                # Set virtual interface as unmanaged in NetworkManager if possible
                if (self.netmanager.networkmanager_is_running() and self.netmanager.NM_OLDER_VERSION == 0):
                    print(f"Network Manager found, set {self.config['vwifi_iface']} as unmanaged device... ")
                    try:
                        self.netmanager.networkmanager_add_unmanaged(self.config['vwifi_iface'])
                        print("DONE")
                    except Exception as e:
                        self.clean.die(f"Failed to set interface as unmanaged: {str(e)}")

            # Update and save configuration
            try:
                self.config_manager.update_config(self.config)
                self.config_manager.save_config()
            except Exception as e:
                self.clean.die(f"Failed to update configuration: {str(e)}")

            # Create virtual interface
            try:
                self.create_virt_iface()
            except Exception as e:
                self.clean.die(f"Failed to create virtual interface: {str(e)}")

            # Lock mutex for writing interface information
            self.lock.mutex_lock()
            try:
                wifi_iface_file = os.path.join(conf_dir, 'wifi_iface')
                with open(wifi_iface_file, 'w') as f:
                    f.write(self.config['wifi_iface'])
                os.chmod(wifi_iface_file, 0o444)
            finally:
                self.lock.mutex_unlock()

            # Set country code if needed
            if self.config['country'] and self.use_iwconfig:
                try:
                    subprocess.run(
                        ['iw', 'reg', 'set', self.config['country']],
                        check=True
                    )
                except subprocess.CalledProcessError as e:
                    self.clean.die(f"Failed to set country code: {str(e)}")

            # Make interface unmanaged if needed
            try:
                self.make_unmanaged()
            except Exception as e:
                self.clean.die(f"Failed to make interface unmanaged: {str(e)}")

            # Print configuration information
            if self.config['hidden']:
                print("Access Point's SSID is hidden!")
            if self.config['mac_filter']:
                print("MAC address filtering is enabled!")
            if self.config['isolate_clients']:
                print("Access Point's clients will be isolated!")

            # Configure services
            try:
                self.config_hostapd()
                self.config_dnsmasq()
                self.init_wifi_iface()
                self.enable_internet_sharing()
                self.start_dhcp_dns()
                self.start_ap()
                self.start_hostapd()
            except Exception as e:
                self.clean.die(f"Failed to configure services: {str(e)}")

            # Exit cleanly
            self.clean.clean_exit("Success")

        except Exception as e:
            self.clean.die(f"Initialization failed: {str(e)}")

    def start_ap(self):
        print(f"hostapd command-line interface: hostapd_cli -p {self.conf_dir}/hostapd_ctrl")
        if self.config['no_haveged']:
            self.haveged_watchdog()
            # HAVEGED_WATCHDOG_PID =

    def enable_internet_sharing(self):
        """Enable Internet sharing using the specified method."""
        if self.config['share_method'] != 'none':
            print(f"Sharing Internet using method: {self.config['share_method']}")

            if self.config['share_method'] == "nat":
                try:
                    # Set up NAT rules
                    gateway_network = f"{'.'.join(self.config['gateway'].split('.')[:3])}.0/24"

                    # Masquerade traffic from the WiFi network
                    subprocess.run([
                        'iptables', '-w', '-t', 'nat', '-I', 'POSTROUTING',
                        '-s', gateway_network,
                        '!', '-o', self.config['wifi_iface'],
                        '-j', 'MASQUERADE'
                    ], check=True)

                    # Allow forwarding from WiFi to internet
                    subprocess.run([
                        'iptables', '-w', '-I', 'FORWARD',
                        '-i', self.config['wifi_iface'],
                        '-s', gateway_network,
                        '-j', 'ACCEPT'
                    ], check=True)

                    # Allow forwarding from internet to WiFi
                    subprocess.run([
                        'iptables', '-w', '-I', 'FORWARD',
                        '-i', self.config['internet_iface'],
                        '-d', gateway_network,
                        '-j', 'ACCEPT'
                    ], check=True)

                    # Enable IP forwarding for the internet interface
                    with open(f"/proc/sys/net/ipv4/conf/{self.config['internet_iface']}/forwarding", 'w') as f:
                        f.write('1')

                    # Enable IP forwarding globally
                    with open("/proc/sys/net/ipv4/ip_forward", 'w') as f:
                        f.write('1')

                    # Load nf_nat_pptp module for PPTP support
                    subprocess.run(['modprobe', 'nf_nat_pptp'], capture_output=True)

                except (subprocess.CalledProcessError, IOError) as e:
                    self.clean.die(f"Failed to set up NAT rules: {str(e)}")

            elif self.config['share_method'] == "bridge":
                try:
                    # Disable iptables rules for bridged interfaces
                    if os.path.exists("/proc/sys/net/bridge/bridge-nf-call-iptables"):
                        with open("/proc/sys/net/bridge/bridge-nf-call-iptables", 'w') as f:
                            f.write('0')

                    """
                    To initialize the bridge interface correctly we need to do the following:

                    1) Save the IPs and route table of INTERNET_IFACE
                    2) If NetworkManager is running set INTERNET_IFACE as unmanaged
                    3) Create BRIDGE_IFACE and attach INTERNET_IFACE to it
                    4) Set the previously saved IPs and route table to BRIDGE_IFACE

                    We need the above because BRIDGE_IFACE is the master interface from now on
                    and it must know where it's connected, otherwise connection is lost.
                    """

                    if not self.is_bridge_interface(self.config['internet_iface']):
                        print("Create a bridge interface... ", end='')

                        # Save current IP addresses and routes
                        ip_output = subprocess.run(
                            ['ip', 'addr', 'show', self.config['internet_iface']],
                            capture_output=True, text=True, check=True
                        ).stdout

                        # Extract IP addresses
                        ip_addrs = []
                        for line in ip_output.splitlines():
                            if 'inet ' in line:
                                ip_addrs.append(line.strip())

                        # Save current routes
                        route_output = subprocess.run(
                            ['ip', 'route', 'show', 'dev', self.config['internet_iface']],
                            capture_output=True, text=True, check=True
                        ).stdout
                        route_addrs = [r.strip() for r in route_output.splitlines() if r.strip()]

                        # Handle NetworkManager if running
                        if self.netmanager.networkmanager_is_running():
                            self.netmanager.networkmanager_add_unmanaged(self.config['internet_iface'])
                            self.netmanager.networkmanager_wait_until_unmanaged(self.config['internet_iface'])

                        # Create bridge interface
                        subprocess.run([
                            'ip', 'link', 'add', 'name', self.config['bridge_iface'],
                            'type', 'bridge'
                        ], check=True)

                        subprocess.run([
                            'ip', 'link', 'set', 'dev', self.config['bridge_iface'], 'up'
                        ], check=True)

                        # Set 0ms forward delay
                        with open(f"/sys/class/net/{self.config['bridge_iface']}/bridge/forward_delay", 'w') as f:
                            f.write('0')

                        # Attach internet interface to bridge interface
                        subprocess.run([
                            'ip', 'link', 'set', 'dev', self.config['internet_iface'],
                            'promisc', 'on'
                        ], check=True)

                        subprocess.run([
                            'ip', 'link', 'set', 'dev', self.config['internet_iface'], 'up'
                        ], check=True)

                        subprocess.run([
                            'ip', 'link', 'set', 'dev', self.config['internet_iface'],
                            'master', self.config['bridge_iface']
                        ], check=True)

                        # Flush old IP addresses
                        subprocess.run([
                            'ip', 'addr', 'flush', self.config['internet_iface']
                        ], check=True)

                        # Add saved IP addresses to bridge interface
                        for addr in ip_addrs:
                            # Clean up the address string
                            clean_addr = addr.replace('inet ', '').replace(' secondary', '').replace(' dynamic', '')
                            clean_addr = re.sub(r'(\d+)sec', r'\1', clean_addr)
                            clean_addr = clean_addr.replace(f' {self.config["internet_iface"]}', '')

                            subprocess.run([
                                'ip', 'addr', 'add', clean_addr, 'dev', self.config['bridge_iface']
                            ], check=True)

                        # Flush old routes
                        subprocess.run([
                            'ip', 'route', 'flush', 'dev', self.config['internet_iface']
                        ], check=True)

                        subprocess.run([
                            'ip', 'route', 'flush', 'dev', self.config['bridge_iface']
                        ], check=True)

                        # Add saved routes to bridge interface
                        # First add non-default routes
                        for route in route_addrs:
                            if not route.startswith('default'):
                                subprocess.run([
                                    'ip', 'route', 'add', route, 'dev', self.config['bridge_iface']
                                ], check=True)

                        # Then add default routes
                        for route in route_addrs:
                            if route.startswith('default'):
                                subprocess.run([
                                    'ip', 'route', 'add', route, 'dev', self.config['bridge_iface']
                                ], check=True)

                        print(f"{self.config['bridge_iface']} created.")

                except (subprocess.CalledProcessError, IOError) as e:
                    self.clean.die(f"Failed to set up bridge: {str(e)}")
        else:
            print("No Internet sharing")

    def start_hostapd(self):
        """Start hostapd with proper error handling and output buffering."""
        # Check if stdbuf is available for unbuffered output
        stdbuf_path = None
        try:
            result = subprocess.run(['which', 'stdbuf'],
                                    capture_output=True, text=True,
                                    check=True)
            stdbuf_path = result.stdout.strip()
        except subprocess.CalledProcessError:
            pass

        # Build the hostapd command
        hostapd_cmd = []
        if stdbuf_path:
            hostapd_cmd.extend([stdbuf_path, '-oL'])

        hostapd_cmd.extend([
            self.config['hostapd_path'],
            *self.config.get('hostapd_debug_args', []),
            os.path.join(self.conf_dir, 'hostapd.conf')
        ])

        # Start hostapd in the background
        try:
            # Use Popen instead of run to get the process object
            self.hostapd_process = subprocess.Popen(
                hostapd_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Save the PID
            self.hostapd_pid = self.hostapd_process.pid
            with open(os.path.join(self.conf_dir, 'hostapd.pid'), 'w') as f:
                f.write(str(self.hostapd_pid))

            # Wait for the process to complete
            return_code = self.hostapd_process.wait()

            if return_code != 0:
                # Print error message if hostapd failed
                error_msg = self.hostapd_process.stderr.read() if self.hostapd_process.stderr else ""
                print("Error: Failed to run hostapd, maybe a program is interfering.")
                print(f"Hostapd error output:\n{error_msg}")

                # NetworkManager specific suggestions
                if self.netmanager.networkmanager_is_running():
                    print("If an error like 'n80211: Could not configure driver mode' was thrown, "
                        "try running the following before starting ap_manager:")

                    if self.nm_older_version:
                        print("    nmcli nm wifi off")
                    else:
                        print("    nmcli r wifi off")

                    print("    rfkill unblock wlan")

                # Clean up and exit
                self.die("Hostapd failed to start")

        except Exception as e:
            print(f"Error starting hostapd: {str(e)}")
            self.die("Failed to start hostapd process")

    def start_dhcp_dns(self):
        """Start DHCP and DNS services with proper error handling."""
        if self.config['share_method'] != 'bridge':
            # Configure DNS if not disabled
            if not self.config.get('no_dns', False):
                dns_port = self.config.get('dns_port', 5353)

                # Set up iptables rules for DNS
                try:
                    # Allow TCP DNS traffic
                    subprocess.run([
                        'iptables', '-w', '-I', 'INPUT',
                        '-p', 'tcp', '-m', 'tcp',
                        '--dport', str(dns_port),
                        '-j', 'ACCEPT'
                    ], check=True)

                    # Allow UDP DNS traffic
                    subprocess.run([
                        'iptables', '-w', '-I', 'INPUT',
                        '-p', 'udp', '-m', 'udp',
                        '--dport', str(dns_port),
                        '-j', 'ACCEPT'
                    ], check=True)

                    # Redirect TCP DNS traffic to our port
                    gateway_network = f"{'.'.join(self.config['gateway'].split('.')[:3])}.0/24"
                    subprocess.run([
                        'iptables', '-w', '-t', 'nat', '-I', 'PREROUTING',
                        '-s', gateway_network,
                        '-d', self.config['gateway'],
                        '-p', 'tcp', '-m', 'tcp',
                        '--dport', '53',
                        '-j', 'REDIRECT', '--to-ports', str(dns_port)
                    ], check=True)

                    # Redirect UDP DNS traffic to our port
                    subprocess.run([
                        'iptables', '-w', '-t', 'nat', '-I', 'PREROUTING',
                        '-s', gateway_network,
                        '-d', self.config['gateway'],
                        '-p', 'udp', '-m', 'udp',
                        '--dport', '53',
                        '-j', 'REDIRECT', '--to-ports', str(dns_port)
                    ], check=True)

                except subprocess.CalledProcessError as e:
                    self.clean.die(f"Failed to set up iptables rules for DNS: {str(e)}")

            # Start dnsmasq if not disabled
            if not self.config.get('no_dnsmasq', False):
                try:
                    # Allow DHCP traffic
                    subprocess.run([
                        'iptables', '-w', '-I', 'INPUT',
                        '-p', 'udp', '-m', 'udp',
                        '--dport', '67',
                        '-j', 'ACCEPT'
                    ], check=True)

                    # Handle AppArmor restrictions
                    complain_cmd = None
                    try:
                        # Check for complain command
                        result = subprocess.run(
                            ['command', '-v', 'complain'],
                            capture_output=True, text=True, check=True
                        )
                        complain_cmd = result.stdout.strip()
                    except subprocess.CalledProcessError:
                        try:
                            # Check for aa-complain command
                            result = subprocess.run(
                                ['command', '-v', 'aa-complain'],
                                capture_output=True, text=True, check=True
                            )
                            complain_cmd = result.stdout.strip()
                        except subprocess.CalledProcessError:
                            pass

                    if complain_cmd:
                        subprocess.run([complain_cmd, 'dnsmasq'], check=True)

                    # Set umask and start dnsmasq
                    old_umask = os.umask(0o033)
                    try:
                        subprocess.run([
                            'dnsmasq',
                            '-C', os.path.join(self.conf_dir, 'dnsmasq.conf'),
                            '-x', os.path.join(self.conf_dir, 'dnsmasq.pid'),
                            '-l', os.path.join(self.conf_dir, 'dnsmasq.leases'),
                            '-p', str(self.config.get('dns_port', 5353))
                        ], check=True)
                    finally:
                        # Restore original umask
                        os.umask(old_umask)

                except subprocess.CalledProcessError as e:
                    self.clean.die(f"Failed to start dnsmasq: {str(e)}")

    def init_wifi_iface(self):
        """Initialize the WiFi interface with proper configuration."""
        try:
            # Set MAC address if virtualization is enabled and MAC is specified
            if not self.config.get('no_virt', False) and self.config.get('mac'):
                subprocess.run([
                    'ip', 'link', 'set', 'dev', self.config['wifi_iface'],
                    'address', self.config['mac']
                ], check=True)

            # Bring interface down and flush addresses
            subprocess.run([
                'ip', 'link', 'set', 'down', 'dev', self.config['wifi_iface']
            ], check=True)

            subprocess.run([
                'ip', 'addr', 'flush', self.config['wifi_iface']
            ], check=True)

            # Set MAC address if virtualization is disabled and MAC is specified
            if self.config.get('no_virt', False) and self.config.get('mac'):
                subprocess.run([
                    'ip', 'link', 'set', 'dev', self.config['wifi_iface'],
                    'address', self.config['mac']
                ], check=True)

            # Configure interface for non-bridge sharing method
            if self.config.get('share_method', 'none') != 'bridge':
                # Bring interface up
                subprocess.run([
                    'ip', 'link', 'set', 'up', 'dev', self.config['wifi_iface']
                ], check=True)

                # Set IP address and broadcast
                gateway = self.config['gateway']
                broadcast = f"{'.'.join(gateway.split('.')[:3])}.255"

                subprocess.run([
                    'ip', 'addr', 'add', f"{gateway}/24",
                    'broadcast', broadcast,
                    'dev', self.config['wifi_iface']
                ], check=True)

            return True

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to initialize WiFi interface: {str(e)}"
            if hasattr(self, 'virt_diems'):
                error_msg += f"\n{self.virt_diems}"
            self.clean.die(error_msg)

    def config_dnsmasq(self):
        """Configure dnsmasq for DHCP and DNS services."""
        try:
            # Determine dnsmasq version and appropriate bind option
            dnsmasq_ver = subprocess.run(
                ['dnsmasq', '-v'],
                capture_output=True, text=True, check=True
            ).stdout.strip()

            # Extract version number and compare
            version_match = re.search(r'[0-9]+(\.[0-9]+)*\.[0-9]+', dnsmasq_ver)
            if version_match and self.version_cmp(version_match.group(0), "2.63") == 1:
                dnsmasq_bind = "bind-interfaces"
            else:
                dnsmasq_bind = "bind-dynamic"

            # Set DNS server address
            dhcp_dns = self.config.get('dhcp_dns', 'gateway')
            if dhcp_dns == "gateway":
                dhcp_dns = self.config['gateway']

            # Write dnsmasq configuration
            with open(os.path.join(self.conf_dir, 'dnsmasq.conf'), 'w') as f:
                f.write(f"listen-address={self.config['gateway']}\n")
                f.write(f"{dnsmasq_bind}\n")
                f.write(f"dhcp-range={self.config['gateway'][:-1]}1,{self.config['gateway'][:-1]}254,255.255.255.0,24h\n")
                f.write(f"dhcp-option-force=option:router,{self.config['gateway']}\n")
                f.write(f"dhcp-option-force=option:dns-server,{dhcp_dns}\n")

                # Add MTU option if available
                mtu = self.get_mtu(self.config['internet_iface'])
                if mtu:
                    f.write(f"dhcp-option-force=option:mtu,{mtu}\n")

                # Disable hosts file if requested
                if not self.config.get('etc_hosts', True):
                    f.write("no-hosts\n")

                # Add additional hosts file if specified
                if self.config.get('addn_hosts'):
                    f.write(f"addn-hosts={self.config['addn_hosts']}\n")

                # Add DHCP hosts if specified
                if self.config.get('dhcp_hosts'):
                    for host in self.config['dhcp_hosts']:
                        f.write(f"dhcp-host={host}\n")

                # Configure DNS logging if specified
                if self.config.get('dns_logfile'):
                    f.write("log-queries\n")
                    f.write(f"log-facility={self.config['dns_logfile']}\n")

                # Redirect all traffic to localhost if requested
                if (self.config.get('share_method') == "none" and
                    self.config.get('redirect_to_localhost', False)):
                    f.write(f"address=/#/{self.config['gateway']}\n")

        except (subprocess.CalledProcessError, IOError, KeyError) as e:
            self.clean.die(f"Failed to configure dnsmasq: {str(e)}")

    def config_hostapd(self):
        """Configure hostapd with all necessary parameters."""
        try:
            # Basic hostapd configuration
            config_lines = [
                "beacon_int=100",
                f"ssid={self.config['ssid']}",
                f"interface={self.config['wifi_iface']}",
                f"driver={self.config['driver']}",
                f"channel={self.config['channel']}",
                f"ctrl_interface={os.path.join(self.conf_dir, 'hostapd_ctrl')}",
                "ctrl_interface_group=0",
                f"ignore_broadcast_ssid={int(self.config.get('hidden', False))}",
                f"ap_isolate={int(self.config.get('isolate_clients', False))}"
            ]

            # Write basic configuration
            with open(os.path.join(self.conf_dir, 'hostapd.conf'), 'w') as f:
                f.write('\n'.join(config_lines) + '\n')

                # Add country code if specified
                if self.config.get('country'):
                    f.write(f"country_code={self.config['country']}\n")
                    f.write("ieee80211d=1\n")

                # Set hardware mode based on frequency band
                if float(self.config.get('freq_band', 2.4)) == 2.4:
                    f.write("hw_mode=g\n")
                else:
                    f.write("hw_mode=a\n")

                # MAC address filtering
                if self.config.get('mac_filter'):
                    f.write(f"macaddr_acl={int(self.config['mac_filter'])}\n")
                    if self.config.get('mac_filter_accept'):
                        f.write(f"accept_mac_file={self.config['mac_filter_accept']}\n")

                # IEEE 802.11n configuration
                if self.config.get('ieee80211n', False):
                    f.write("ieee80211n=1\n")
                    if self.config.get('ht_capab'):
                        f.write(f"ht_capab={self.config['ht_capab']}\n")

                # IEEE 802.11ac configuration
                if self.config.get('ieee80211ac', False):
                    f.write("ieee80211ac=1\n")

                # IEEE 802.11ax configuration
                if self.config.get('ieee80211ax', False):
                    f.write("ieee80211ax=1\n")

                # VHT capabilities
                if self.config.get('vht_capab'):
                    f.write(f"vht_capab={self.config['vht_capab']}\n")

                # WMM enabled for n/ac
                if self.config.get('ieee80211n', False) or self.config.get('ieee80211ac', False):
                    f.write("wmm_enabled=1\n")

                # WPA/WPA2 configuration
                if self.config.get('password'):
                    # Handle WPA version
                    wpa_version = self.config.get('wpa_version', '2')
                    if wpa_version == "1+2":
                        wpa_version = "2"  # Default to WPA2 for "1+2" setting

                    # Determine key type
                    wpa_key_type = "passphrase" if not self.config.get('use_psk', False) else "psk"

                    if wpa_version == "3":
                        # WPA3 Transition Mode configuration
                        f.write("wpa=2\n")
                        f.write(f"wpa_{wpa_key_type}={self.config['password']}\n")
                        f.write("wpa_key_mgmt=WPA-PSK SAE\n")
                        f.write("wpa_pairwise=CCMP\n")
                        f.write("rsn_pairwise=CCMP\n")
                        f.write("ieee80211w=1\n")
                    else:
                        # Standard WPA/WPA2 configuration
                        f.write(f"wpa={wpa_version}\n")
                        f.write(f"wpa_{wpa_key_type}={self.config['password']}\n")
                        f.write("wpa_key_mgmt=WPA-PSK\n")
                        f.write("wpa_pairwise=CCMP\n")
                        f.write("rsn_pairwise=CCMP\n")

                # Bridge configuration
                if self.config.get('share_method') == "bridge":
                    f.write(f"bridge={self.config['bridge_iface']}\n")

            # Configure dnsmasq if not using bridge and not disabled
            if self.config.get('share_method') != "bridge" and not self.config.get('no_dnsmasq', False):
                self.config_dnsmasq()

            return True

        except (IOError, KeyError) as e:
            self.clean.die(f"Failed to configure hostapd: {str(e)}")

    def make_unmanaged(self):
        if self.netmanager.networkmanager_exists() and self.netmanager.networkmanager_iface_is_unmanaged(self.config['wifi_iface']):
            print(f"Network Manager found, set {self.config['wifi_iface']} as unmanaged device... ")
            self.netmanager.networkmanager_add_unmanaged(self.config['wifi_iface'])

            if self.netmanager.networkmanager_is_running():
                self.netmanager.networkmanager_wait_until_unmanaged(self.config['wifi_iface'])
            print("DONE")

    def iface_freq_channel_setup(self):
        # Set correct frequency and channel
        if self.is_wifi_connected(self.config['wifi_iface']):
            if not self.config['freq_band']:
                wifi_iface_freq = self.netmanager._get_interface_freq_(self.config['wifi_iface'])
                wifi_iface_channel = self.ieee80211_frequency_to_channel(iw_freq)

                print(f"{self.config['wifi_iface']} is already associated with channel {wifi_iface_channel} ({wifi_iface_freq} MHz)")

                self.config.update({'freq_band': 5}) if self.is_5ghz_frequency(iw_freq) else self.config.update({'freq_band': 2.4})

                if wifi_iface_channel != wifi_iface_channel:
                    if self._get_channels_() >= 2 and self.can_transmit_to_channel(self.config['wifi_iface'], self.config['channel']):
                        print("multiple channels supported")
                    else:
                        # Fallback to currently connected channel if the adapter can not transmit to the default channel (1)
                        print(f"multiple channels not supported, fallback to channel: {wifi_iface_channel}")
                        self.config.update({'channel': wifi_iface_channel})
                        if self.can_transmit_to_channel(self.config['wifi_iface'], self.config['channel']):
                            print(f"Transmitting to channel {self.config['channel']}...")
                        else:
                            sys.exit(f"Your adapter can not transmit to channel {self.config['channel']}, frequency band {self.config['freq_band']}GHz.")
                else:
                    print(f"channel: {self.config['channel']}")

            else:
                print(f"Custom frequency band set with {self.config['freq_band']}Ghz with channel {self.config['channel']}")

    def create_virt_iface(self):
        print("Creating a virtual WiFi interface... ")

        if subprocess.run(['iw', 'dev', self.config['wifi_iface'], 'interface', 'add', self.config['vwifi_iface'], 'type', '__ap'], check=True, capture_output=True, text=True).returncode == 0:
            # now we can call networkmanager_wait_until_unmanaged
            if self.netmanager.networkmanager_is_running() and self.netmanager.networkmanager_wait_until_unmanaged(self.config['vwifi_iface']):
                print(f"{self.config['wifi_iface']} created")
        else:
            sys.exit(self.virt_diems)

        old_mac = self.get_macaddr(self.config['vwifi_iface'])
        new_mac = self.config['mac']
        if new_mac and new_mac not in self.get_all_macaddrs:
            new_mac = self.get_new_macaddr(self.config['vwifi_iface'])
            self.config.update({'mac': new_mac})
            self.config.update({'wifi_iface': self.config['vwifi_iface']})

    def _get_channels_(self) -> bool:
        adapter_info = self.get_adapter_info()
        return bool(re.search(r'channels\s<=\s2', adapter_info))

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

    def start_hotspot(self):
        """Start the hotspot"""
        if not self.check_dependencies():
            return False

        print(f"Starting hotspot with SSID: {self.config['ssid']}")

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

    def stop_hotspot(self):
        """Stop the hotspot using appropriate network management tools."""
        print(f"Stopping {self.config['vwifi_iface']}...")

        try:
            if self.config['mode'] == 'nmcli':
                # Use NetworkManager CLI for stopping and deleting the connection
                subprocess.run(['nmcli', 'con', 'down', self.config['vwifi_iface']],
                               check=True, capture_output=True)
                subprocess.run(['nmcli', 'con', 'delete', self.config['vwifi_iface']],
                               check=True, capture_output=True)
            else:
                # Stop hostapd service
                subprocess.run(['systemctl', 'stop', 'hostapd'],
                               check=True, capture_output=True)

                # Stop systemd-networkd service
                subprocess.run(['systemctl', 'stop', 'systemd-networkd'],
                               check=True, capture_output=True)

                # Restart NetworkManager
                subprocess.run(['systemctl', 'start', 'NetworkManager'],
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
            subprocess.run(['ip', 'link', 'set', 'dev', self.config['vwifi_iface'], 'down'],
                           check=True, capture_output=True)

            # Flush IP addresses
            subprocess.run(['ip', 'addr', 'flush', self.config['vwifi_iface']],
                           check=True, capture_output=True)

            # Remove the interface if it's a virtual interface
            if not self.config.get('no_virt', False):
                subprocess.run(['iw', 'dev', self.config['vwifi_iface'], 'del'],
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

    def is_5ghz_frequency(self, freq=None):
        """Check if frequency is in 5GHz band"""
        return bool(re.match(r'^(49[0-9]{2})|(5[0-9]{3})(\.0+)?$', str(freq)))

    def is_wifi_connected(self, iface=None):
        """Check if WiFi interface is connected"""
        iface = iface if iface else self.config['wifi_iface']

        if not self.use_iwconfig:
            try:
                result = subprocess.run(['iw', 'dev', iface, 'link'],
                                        capture_output=True, text=True, check=True)
                return 'Connected to' in result.stdout
            except subprocess.CalledProcessError:
                return False
        else:
            try:
                result = subprocess.run(['iwconfig', iface],
                                        capture_output=True, text=True, check=True)
                return bool(re.search(r'Access Point: [0-9a-fA-F]{2}:', result.stdout))
            except subprocess.CalledProcessError:
                return False

    def is_macaddr(self, mac=None):
        """Check if string is a valid MAC address"""
        mac = mac if mac else self.config['mac']
        if not mac:
            return False
        return bool(re.match(r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$', mac))

    def is_unicast_macaddr(self, mac=None):
        """Check if MAC address is unicast"""
        mac = mac if mac else self.config['mac']
        if not self.is_macaddr(mac):
            return False
        first_byte = int(mac.split(':')[0], 16)
        return first_byte % 2 == 0

    def get_macaddr(self, iface=None):
        """Get MAC address of an interface"""
        iface = iface if iface else self.config['wifi_iface']
        if not self.is_interface(iface):
            return None
        try:
            with open(f"/sys/class/net/{iface}/address", 'r') as f:
                return f.read().strip()
        except IOError:
            return None

    def get_mtu(self, iface=None) -> int:
        """Get MTU of an interface"""
        iface = iface if iface else self.config['wifi_iface']

        if not self.is_interface(iface):
            return None
        try:
            with open(f"/sys/class/net/{iface}/mtu", 'r') as f:
                return int(f.read().strip())
        except (IOError, ValueError):
            return None

    def alloc_new_iface(self, prefix=None):
        """Allocate a new interface name"""
        prefix = prefix if prefix else self.config['wifi_iface']
        COMMON_CONFDIR = self.config['common_conf_dir'] or config_manager.__bconfdir__
        i = 0
        self.lock.mutex_lock()
        try:
            while True:
                iface_name = f"{prefix}{i}"
                if not self.is_interface(iface_name) and not os.path.exists(f"{COMMON_CONFDIR}/ifaces/{iface_name}"):
                    os.makedirs(f"{COMMON_CONFDIR}/ifaces", exist_ok=True)
                    with open(f"{COMMON_CONFDIR}/ifaces/{iface_name}", 'w'):
                        pass  # Just create the file
                    self.lock.mutex_unlock()
                    return iface_name
                i += 1
        finally:
            self.lock.mutex_unlock()

    def dalloc_iface(self, iface=None):
        """Allocate a new interface name"""
        prefix = iface if iface else self.config['wifi_iface']
        COMMON_CONFDIR = self.config['common_conf_dir'] or config_manager.__bconfdir__
        i = 0
        self.lock.mutex_lock()
        try:
            iface_name = f"{prefix}{i}"
            if not self.is_interface(iface_name) and not os.path.exists(f"{COMMON_CONFDIR}/ifaces/{iface_name}"):
                os.remove(f"{COMMON_CONFDIR}/ifaces/{iface_name}")

                self.lock.mutex_unlock()
                return iface_name
            i += 1
        finally:
            self.lock.mutex_unlock()

    def is_interface(self, iface=None):
        """Check if interface exists"""
        iface = iface if iface else self.config['wifi_iface']
        return os.path.exists(f"/sys/class/net/{iface}")

    @property
    def has_hostapd(self):
        return subprocess.run(['which', 'hostapd'], check=True, capture_output=True).returncode == 0

    @property
    def where_hostapd(self):
        return subprocess.run(['which', 'hostapd'], check=True, capture_output=True, text=True).stdout

    def can_transmit_to_channel(self, iface=None, channel=None):
        iface = iface if iface else self.config['wifi_iface']
        channel = channel if channel else self.config['channel']

        if not self.use_iwconfig:
            # Determine frequency band pattern
            if self.freq_band == 2.4:
                pattern = rf" 24[0-9][0-9](?:\.0+)? MHz \[{channel}\]"
            else:
                pattern = rf" (49[0-9][0-9]|5[0-9]{{3}})(?:\.0+)? MHz \[{channel}\]"

            # Get adapter info and check channel
            adapter_info = self.get_adapter_info(iface)
            channel_info = re.search(pattern, adapter_info)

            if not channel_info:
                return False

            channel_str = channel_info.group(0)
            if "no IR" in channel_str or "disabled" in channel_str:
                return False

            return True
        else:
            # Format channel number with leading zero
            formatted_channel = f"{channel:02d}"

            # Check channel using iwlist
            iwlist_output = self.run_command(f"iwlist {iface} channel")
            pattern = rf"Channel\s+{formatted_channel}\s?:"
            channel_info = re.search(pattern, iwlist_output)

            return bool(channel_info)

    def can_be_ap(self):
        # iwconfig does not provide this information, assume true
        if self.use_iwconfig:
            return True

        adapter_info = self.get_adapter_info()
        if re.search(r'{\s*AP\s*}', adapter_info):
            return True

        return False

    def can_be_sta_and_ap(self, iface=None):
        # iwconfig does not provide this information, assume false
        if self.use_iwconfig:
            return False

        if self.get_adapter_kernel_module(iface) == "brcmfmac":
            warning = """WARN: brmfmac driver doesn't work properly with virtual interfaces and
            it can cause kernel panic. For this reason we disallow virtual
            interfaces for your adapter.
            For more info: https://github.com/skye-cyber/ap_manager/issues/203"""
            print(warning)
            return False

        # Check if adapter supports both STA and AP modes
        adapter_info = self.get_adapter_info()
        if re.search(r'{\s*managed\s*AP\s*}', adapter_info) or re.search(r'{\s*AP\s*managed\s*}', adapter_info):
            return True

        return False

    def get_adapter_kernel_module(self, _iface=None) -> str:
        iface = _iface if _iface else self.config['wifi_iface']
        module_path = os.path.realpath(f"/sys/class/net/{iface}/device/driver/module")
        module_name = os.path.basename(module_path)
        print(module_name)
        return module_name

    def get_adapter_info(self, iface=None) -> str:
        iface = _iface if _iface else self.config['wifi_iface']

        PHY = self.get_phy_device(iface)
        if not PHY:
            return None

        result = subprocess.run(['iw', 'phy', PHY, 'info'], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else None

    def get_phy_device(self, iface=None) -> str:
        t_iface = iface if iface else self.config['wifi_iface']
        c_dir = '/sys/class/ieee80211/'

        for x in os.listdir(c_dir):
            if x == t_iface or t_iface in x:  # check partial match
                return x
            elif os.path.exists(f"{c_dir}/{x}/device/net/{t_iface}"):
                return x
            elif os.path.exists(f"{c_dir}/{x}/device/net:{t_iface}"):
                return x

        print("Failed to get phy interface")
        return None

    def is_bridge_interface(self, _iface=None):
        iface = _iface if _iface else self.config['wifi_iface']
        return os.path.exists(f"/sys/class/net/{iface}/bridge")

    def is_wifi_interface(self, _iface=None):
        iface = _iface if _iface else self.config['wifi_iface']

        try:
            # Check if 'iw' command exists and works
            if subprocess.run(['which', 'iw'], check=True, capture_output=True).returncode == 0:
                result = subprocess.run(['iw', 'dev', iface, 'info'], capture_output=True)
                if result.returncode == 0:
                    return True

            # Check if 'iwconfig' command exists and works
            if subprocess.run(['which', 'iwconfig'], check=True, capture_output=True).returncode == 0:
                result = subprocess.run(['iwconfig', iface], capture_output=True)
                if result.returncode == 0:
                    self.use_iwconfig = True
                    return True

            return False
        except subprocess.CalledProcessError:
            return False

    @property
    def get_all_macaddrs(self) -> list:
        """Get all MAC addresses from all network interfaces"""
        macs = []
        net_dir = "/sys/class/net/"
        try:
            for iface in os.listdir(net_dir):
                addr_path = os.path.join(net_dir, iface, "address")
                if os.path.exists(addr_path):
                    with open(addr_path, 'r') as f:
                        mac = f.read().strip()
                        if self.is_macaddr(mac):
                            macs.append(mac)
        except OSError:
            pass
        return macs

    def get_new_macaddr(self, iface=None):
        """Generate a new MAC address based on the current one"""
        iface = iface if iface else self.config['wifi_iface']

        old_mac = self.get_macaddr(iface)
        if not old_mac:
            return None

        # Extract the last byte and convert to integer
        last_byte_hex = old_mac.split(':')[-1]
        last_byte = int(last_byte_hex, 16)

        self.mutex_lock()
        try:
            for i in range(1, 256):
                new_byte = (last_byte + i) % 256
                new_mac = f"{old_mac.rsplit(':', 1)[0]}:{new_byte:02x}"

                # Check if MAC address is already in use
                all_macs = self.get_all_macaddrs()
                if new_mac not in all_macs:
                    return new_mac
        finally:
            self.mutex_unlock()

        return None

    def haveged_watchdog(self):
        """Monitor system entropy and start haveged if needed"""
        show_warn = True
        while True:
            try:
                with open('/proc/sys/kernel/random/entropy_avail', 'r') as f:
                    entropy = int(f.read().strip())

                if entropy < 1000:
                    if not self.is_haveged_installed():
                        if show_warn:
                            print("WARN: Low entropy detected. We recommend you to install 'haveged'")
                            show_warn = False
                    elif not self.is_haveged_running():
                        print("Low entropy detected, starting haveged")
                       self.mutex_lock()
                        try:
                            # Start haveged with a specific PID file
                            subprocess.Popen(['haveged', '-w', '1024', '-p',
                                            os.path.join(COMMON_CONFDIR, 'haveged.pid')])
                        finally:
                            self.mutex_unlock()
            except (IOError, ValueError):
                pass

            time.sleep(2)

    def is_haveged_installed():
        """Check if haveged is installed"""
        try:
            subprocess.run(['which', 'haveged'],
                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False

    def is_haveged_running():
        """Check if haveged is running (HAVE GEnerated Daemon)"""
        try:
            subprocess.run(['pidof', 'haveged'],
                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False

    def start_haveged_watchdog():
        """Start the haveged watchdog in a background thread"""
        thread = Thread(target=haveged_watchdog, daemon=True)
        thread.start()
        return thread

    def get_wifi_iface_from_pid(self, pid: str) -> Optional[str]:
        """Get the WiFi interface associated with a process ID."""
        running = self.list_running()
        for entry in running:
            parts = entry.split()
            if parts[0] == pid:
                # Return the last field (interface name)
                return parts[-1].rstrip(')')
        return None

    def get_pid_from_wifi_iface(self, wifi_iface: str) -> Optional[str]:
        """Get the process ID associated with a WiFi interface."""
        running = self.list_running()
        for entry in running:
            parts = entry.split()
            if wifi_iface in parts[-1]:
                return parts[0]
        return None

    def get_confdir_from_pid(self, pid: str) -> Optional[str]:
        """Get the configuration directory for a process ID."""
        self.mutex_lock()
        try:
            for conf_dir in self.list_running_conf():
                pid_file = os.path.join(conf_dir, 'pid')
                if os.path.exists(pid_file):
                    with open(pid_file, 'r') as f:
                        if f.read().strip() == pid:
                            return conf_dir
            return None
        finally:
            self.mutex_unlock()

    def print_client(self, mac: str) -> None:
        """Print client information in a formatted way."""
        ipaddr = "*"
        hostname = "*"

        # Check dnsmasq leases file
        dnsmasq_leases = os.path.join(self.conf_dir, 'dnsmasq.leases')
        if os.path.exists(dnsmasq_leases):
            with open(dnsmasq_leases, 'r') as f:
                for line in f:
                    if mac in line:
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            ipaddr = parts[2]
                            hostname = parts[3]

        print(f"{mac:<20} {ipaddr:<18} {hostname}")

    def list_clients(self, pid_or_iface: str) -> None:
        """List all clients connected to a specific instance."""
        wifi_iface = ""
        pid = ""

        # If argument is a PID, get the associated WiFi interface
        if pid_or_iface.isdigit():
            pid = pid_or_iface
            wifi_iface = self.get_wifi_iface_from_pid(pid)
            if not wifi_iface:
                sys.exit(f"Error: '{pid}' is not the PID of a running {self.prog_name} instance.")
        else:
            wifi_iface = pid_or_iface

        # Verify it's a WiFi interface
        if not self.is_wifi_interface(wifi_iface):
            sys.exit(f"Error: '{wifi_iface}' is not a WiFi interface.")

        # Get PID if not already set
        if not pid:
            pid = self.get_pid_from_wifi_iface(wifi_iface)
            if not pid:
                sys.exit(f"Error: '{wifi_iface}' is not used from {self.prog_name} instance.\n"
                         f"Maybe you need to pass the virtual interface instead.\n"
                         f"Use --list-running to find it out.")

        # Get configuration directory
        self.conf_dir = self.get_confdir_from_pid(pid)
        if not self.conf_dir:
            sys.exit(f"Error: Could not find configuration directory for PID {pid}")

        # List clients using iw if available
        if not self.config.get('use_iwconfig', False):
            try:
                result = subprocess.run(
                    ['iw', 'dev', wifi_iface, 'station', 'dump'],
                    capture_output=True, text=True, check=True
                )

                # Extract MAC addresses
                macs = []
                for line in result.stdout.splitlines():
                    if 'Station' in line:
                        mac = line.split()[1]
                        macs.append(mac)

                if not macs:
                    print("No clients connected")
                    return

                # Print header
                print(f"{'MAC':<20} {'IP':<18} {'Hostname'}")

                # Print each client
                for mac in macs:
                    self.print_client(mac)

                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

        # Fallback to error if iwconfig is required
        sys.exit(f"Error: This option is not supported for the current driver.")

    def has_running_instance(self) -> bool:
        """Check if there are any running instances."""
        self.mutex_lock()
        try:
            for proc_dir in os.listdir(self.proc_dir):
                pid_file = os.path.join(self.proc_dir, proc_dir)
                if os.path.exists(pid_file):
                    with open(pid_file, 'r') as f:
                        pid = f.read().strip()
                    if os.path.exists(f'/proc/{pid}'):
                        return True
            return False
        finally:
            self.mutex_unlock()

    def is_running_pid(self, pid: str) -> bool:
        """Check if a specific PID is running."""
        running = self.list_running()
        for entry in running:
            if entry.startswith(pid):
                return True
        return False

    def send_stop(self, pid_or_iface: str) -> None:
        """Send stop signal to a specific instance."""
        self.mutex_lock()
        try:
            # Try to send stop to specific PID
            if self.is_running_pid(pid_or_iface):
                os.kill(int(pid_or_iface), signal.SIGUSR1)
                return

            # Try to send stop to specific interface
            for entry in self.list_running():
                parts = entry.split()
                if pid_or_iface in parts[-1]:
                    os.kill(int(parts[0]), signal.SIGUSR1)
        finally:
            self.mutex_unlock()

    def list_running_conf(self) -> List[str]:
        """List all running configuration directories."""
        self.lock.mutex_lock()

        try:
            running_confs = []
            for conf_dir in os.listdir(self.conf_dir):
                pid_file = os.path.join(self.conf_dir, proc_dir)
                wifi_iface_file = os.path.join(self.conf_dir, conf_dir, 'wifi_iface')

                if os.path.exists(pid_file) and os.path.exists(wifi_iface_file):
                    with open(pid_file, 'r') as f:
                        pid = f.read().strip()
                    if os.path.exists(f'/proc/{pid}'):
                        running_confs.append(pid_file)
            return running_confs
        finally:
            self.lock.mutex_unlock()

    def list_running(self) -> List[str]:
        """List all running instances with their interfaces."""
        self.lock.mutex_lock()
        try:
            running_instances = []
            for conf_dir in self.list_running_conf():
                iface = os.path.basename(conf_dir)
                with open(os.path.join(conf_dir, 'pid'), 'r') as f:
                    pid = f.read().strip()
                with open(os.path.join(conf_dir, 'wifi_iface.pid'), 'r') as f:
                    wifi_iface = f.read().strip()

                if iface == wifi_iface:
                    running_instances.append(f"{pid} {iface}")
                else:
                    running_instances.append(f"{pid} {iface} ({wifi_iface})")
            return running_instances
        finally:
            self.lock.mutex_unlock()
