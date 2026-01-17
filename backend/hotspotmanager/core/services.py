import os
import re
import sys
import subprocess
from ap_utils.colors import fg
from ap_utils.command import command
from ap_utils.config import config_manager
from .netmanager import netmanager
from .shared import shared


class NetServices:
    def __init__(self):
        self.config = config_manager.get_config
        self.proc_dir = self.config['proc_dir']
        self.conf_dir = self.config.get('conf_dir', config_manager.__bconfdir__)

    def __enter__(self):
        self.config = config_manager.get_config

    def configure(self):
        print("configuring")
        self.configure_hostapd()

        # Configure dnsmasq if not using bridge and not disabled
        if self.config.get('share_method') != "bridge" and not self.config.get('no_dnsmasq', False):
            self.configure_dnsmasq()

    def start(self):
        self.enable_internet_sharing()
        self.start_dhcp_dns()
        # self.start_ap()
        self.start_hostapd()

    def configure_hostapd(self):
        """Configure hostapd with all necessary parameters."""
        try:
            print(f"Config: {fg.YELLOW}{os.path.join(self.conf_dir, 'hostapd.conf')}{fg.RESET}")

            # Basic hostapd configuration
            config_lines = [
                # Basic Configuration
                f"interface={self.config['vwifi_iface']}",
                f"ssid={self.config['ssid']}",
                f"driver={self.config['driver']}",
                f"channel={self.config['channel']}",
                f"ctrl_interface={os.path.join(self.conf_dir, 'hostapd_ctrl')}",
                "ctrl_interface_group=0",
                "beacon_int=100",
                "dtim_period=2",
                "max_num_sta=25",

                # Performance Optimization
                "wmm_enabled=1",
                "wmm_ac_bk_cwmin=4",
                "wmm_ac_bk_cwmax=10",
                "wmm_ac_bk_aifs=7",
                "wmm_ac_be_aifs=3",
                "wmm_ac_be_cwmin=4",
                "wmm_ac_be_cwmax=10",
                "wmm_ac_vi_aifs=2",
                "wmm_ac_vi_cwmin=3",
                "wmm_ac_vi_cwmax=4",
                "wmm_ac_vo_aifs=2",
                "wmm_ac_vo_cwmin=2",
                "wmm_ac_vo_cwmax=3",

                # 802.11n Support (HT)
                # ht_capab=[HT40][SHORT-GI-20][DSSS_CCK-40]

                # 802.11ac Support (VHT) - if supported by your hardware
                # ieee80211ac=1
                # vht_oper_chwidth=1
                # vht_capab=[MAX-MPDU-11454][SHORT-GI-80]

                # Quality of Service
                f"ap_isolate={int(self.config.get('isolate_clients', False))}"
                f"ignore_broadcast_ssid={False}",  # int(self.config.get('hidden', False))
                "auth_algs=1",

                # Logging and Debugging
                "logger_syslog=-1",
                "logger_syslog_level=2",
                "logger_stdout=-1",
                "logger_stdout_level=2",

                # Advanced Settings
                "eapol_key_index_workaround=0",
                "eap_server=0",
                "own_ip_addr=127.0.0.1",
            ]

            # Write basic configuration
            print("Write basic configuration")
            with open(os.path.join(self.conf_dir, 'hostapd.conf'), 'w') as f:
                f.write('\n'.join(config_lines) + '\n')

                # Add country code if specified
                print(f"{fg.FCYAN} - Add country code if specified{fg.RESET}")
                if self.config.get('country'):
                    f.write(f"country_code={self.config['country']}\n")
                    f.write("ieee80211d=1\n")
                    f.write("ieee80211h=1\n")

                # Set hardware mode based on frequency band
                print(f"{fg.FCYAN} - Set hardware mode based on frequency band{fg.RESET}")
                print("     ...")
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

            return True

        except (IOError, KeyError) as e:
            sys.exit(f"Failed to configure hostapd: {str(e)}")

    def configure_dnsmasq(self):
        """Configure dnsmasq for DHCP and DNS services."""
        try:
            # Determine dnsmasq version and appropriate bind option
            dnsmasq_ver = subprocess.run(
                ['dnsmasq', '-v'],
                capture_output=True, text=True, check=True
            ).stdout.strip()

            # Extract version number and compare
            version_match = re.search(r'[0-9]+(\.[0-9]+)*\.[0-9]+', dnsmasq_ver)
            if version_match and netmanager.version_cmp(version_match.group(0), "2.63") == 1:
                dnsmasq_bind = "bind-interfaces"
            else:
                dnsmasq_bind = "bind-dynamic"

            # Set DNS server address
            dhcp_dns = self.config.get('dhcp_dns', None)
            if not dhcp_dns:
                dhcp_dns = self.config['gateway']

            # Write dnsmasq configuration
            with open(os.path.join(self.conf_dir, 'dnsmasq.conf'), 'w') as f:
                f.write(f"listen-address={self.config['gateway']}\n")
                f.write(f"{dnsmasq_bind}\n")
                f.write(f"dhcp-range={self.config['gateway'][:-1]}1,{self.config['gateway'][:-1]}254,255.255.255.0,24h\n")
                f.write(f"dhcp-option-force=option:router,{self.config['gateway']}\n")
                f.write(f"dhcp-option-force=option:dns-server,{dhcp_dns}\n")

                # Add MTU option if available
                mtu = shared.get_mtu(self.config['internet_iface'])
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
                if (self.config.get('share_method') == "none"
                        and self.config.get('redirect_to_localhost', False)):
                    f.write(f"address=/#/{self.config['gateway']}\n")

        except (subprocess.CalledProcessError, IOError, KeyError) as e:

            sys.exit(f"Failed to configure dnsmasq: {str(e)}")

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
            with open(os.path.join(self.proc_dir, 'hostapd.pid'), 'w') as f:
                f.write(str(self.hostapd_pid))

            # Wait for the process to complete
            return_code = self.hostapd_process.wait()

            if return_code != 0:
                # Print error message if hostapd failed
                error_msg = self.hostapd_process.stderr.read() if self.hostapd_process.stderr else ""
                print(f"Error: {fg.RED}{self.hostapd_process.stderr.read() or self.hostapd_process.stdout.read()}{fg.RESET}")
                print(f"Hostapd error output:\n{error_msg}")

                # NetworkManager specific suggestions
                if netmanager.networkmanager_is_running():
                    print("If an error like 'n80211: Could not configure driver mode' was thrown, "
                          "try running the following before starting ap_manager:")

                    if self.nm_older_version:
                        print("    nmcli nm wifi off")
                    else:
                        print("    nmcli r wifi off")

                    print("    rfkill unblock wlan")

                # Clean up and exit
                print(f"{fg.RED}Hostapd failed to start{fg.RESET}")

        except Exception as e:
            raise f"Error starting hostapd: {str(e)}"

    def dhcp_service_nodns(self):
        # Configure DNS if not disabled
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
            sys.exit(f"Failed to set up iptables rules for DNS: {str(e)}")

    def dhcp_service_nodnsmasq(self):
        try:
            # Allow DHCP traffic
            command.run([
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
            except Exception:
                pass

            if complain_cmd:
                command.run([complain_cmd, 'dnsmasq'], check=True)

            # Set umask and start dnsmasq
            old_umask = os.umask(0o033)
            try:
                # Start dnsmasq if not running
                # TODO: kill dnsmasq and continue
                if not self.get_dnsmasq_pid():
                    command.run([
                        'dnsmasq',
                        '-C', os.path.join(self.conf_dir, 'dnsmasq.conf'),
                        '-x', os.path.join(self.conf_dir, 'dnsmasq.pid'),
                        '-l', os.path.join(self.conf_dir, 'dnsmasq.leases'),
                        '-p', str(self.config.get('dns_port', 5353))
                    ], check=True)
            except Exception:
                pass
            finally:
                pid = self.get_dnsmasq_pid()
                if pid:
                    print(f"DNSMASQ RUNNING as PID: {fg.CYAN}{pid}{fg.RESET}")

                # Restore original umask
                os.umask(old_umask)

        except subprocess.CalledProcessError as e:
            raise f"Failed to start dnsmasq: {str(e)}"
        except Exception as e:
            print(e)

    def get_dnsmasq_pid(self):
        pid_file = os.path.join(self.conf_dir, 'dnsmasq.pid')
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = f.read()
            return pid
        return

    def start_dhcp_dns(self):
        """Start DHCP and DNS services with proper error handling."""
        if self.config['share_method'] != 'bridge':
            if not self.config.get('no_dns', False):
                self.dhcp_service_nodns()
            # Start dnsmasq if not disabled
            if not self.config.get('no_dnsmasq', False):
                self.dhcp_service_nodnsmasq()

    def enable_internet_sharing(self):
        """Enable Internet sharing using the specified method."""
        if self.config['share_method'] != 'none':
            print(f"Sharing Internet using method: {self.config['share_method']}")

            if self.config['share_method'] == "nat":
                self.nat_sharing()

            elif self.config['share_method'] == "bridge":
                self.bridge_sharing()
        else:
            print("No Internet sharing")

    def nat_sharing(self):
        try:
            # Set up NAT rules
            gateway_network = f"{'.'.join(self.config['gateway'].split('.')[:3])}.0/24"

            # Masquerade traffic from the WiFi network
            command.run([
                'iptables', '-w', '-t', 'nat', '-I', 'POSTROUTING',
                '-s', gateway_network,
                '!', '-o', self.config['wifi_iface'],
                '-j', 'MASQUERADE'
            ], check=True)

            # Allow forwarding from WiFi to internet
            command.run([
                'iptables', '-w', '-I', 'FORWARD',
                '-i', self.config['wifi_iface'],
                '-s', gateway_network,
                '-j', 'ACCEPT'
            ], check=True)

            # Allow forwarding from internet to WiFi
            command.run([
                'iptables', '-w', '-I', 'FORWARD',
                '-i', self.config['internet_iface'],
                '-d', gateway_network,
                '-j', 'ACCEPT'
            ], check=True)

            iface_file = f"/proc/sys/net/ipv4/conf/{self.config['internet_iface']}/forwarding"
            if not os.path.exists(iface_file):
                print("Choose a different internet interface")

            # Enable IP forwarding for the internet interface
            with open(iface_file, 'w') as f:
                f.write('1')

            # Enable IP forwarding globally
            with open("/proc/sys/net/ipv4/ip_forward", 'w') as f:
                f.write('1')

            # Load nf_nat_pptp module for PPTP support
            command.run(['modprobe', 'nf_nat_pptp'], capture_output=True)
            return True
        except (subprocess.CalledProcessError, IOError) as e:
            raise f"Failed to set up NAT rules: {str(e)}"
        except Exception:
            raise

    def bridge_sharing(self):
        try:
            # Disable iptables rules for bridged interfaces
            iptable_rules_file = "/proc/sys/net/bridge/bridge-nf-call-iptables"
            if os.path.exists(iptable_rules_file):
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
                if netmanager.networkmanager_is_running():
                    netmanager.networkmanager_add_unmanaged(self.config['internet_iface'])
                    netmanager.networkmanager_wait_until_unmanaged(self.config['internet_iface'])

                # Create bridge interface
                print("Create bridge interface")
                command.run([
                    'ip', 'link', 'add', 'name', self.config['bridge_iface'],
                    'type', 'bridge'
                ], check=True)

                command.run([
                    'ip', 'link', 'set', 'dev', self.config['bridge_iface'], 'up'
                ], check=True)

                # Set 0ms forward delay
                with open(f"/sys/class/net/{self.config['bridge_iface']}/bridge/forward_delay", 'w') as f:
                    f.write('0')

                # Attach internet interface to bridge interface
                print("Attach internet interface to bridge interface")
                command.run([
                    'ip', 'link', 'set', 'dev', self.config['internet_iface'],
                    'promisc', 'on'
                ], check=True)

                command.run([
                    'ip', 'link', 'set', 'dev', self.config['internet_iface'], 'up'
                ], check=True)

                command.run([
                    'ip', 'link', 'set', 'dev', self.config['internet_iface'],
                    'master', self.config['bridge_iface']
                ], check=True)

                # Flush old IP addresses
                command.run([
                    'ip', 'addr', 'flush', self.config['internet_iface']
                ], check=True)

                # Add saved IP addresses to bridge interface
                for addr in ip_addrs:
                    # Clean up the address string
                    clean_addr = addr.replace('inet ', '').replace(' secondary', '').replace(' dynamic', '')
                    clean_addr = re.sub(r'(\d+)sec', r'\1', clean_addr)
                    clean_addr = clean_addr.replace(f' {self.config["internet_iface"]}', '')

                    command.run([
                        'ip', 'addr', 'add', clean_addr, 'dev', self.config['bridge_iface']
                    ], check=True)

                # Flush old routes
                command.run([
                    'ip', 'route', 'flush', 'dev', self.config['internet_iface']
                ], check=True)

                command.run([
                    'ip', 'route', 'flush', 'dev', self.config['bridge_iface']
                ], check=True)

                # Add saved routes to bridge interface
                # First add non-default routes
                for route in route_addrs:
                    if not route.startswith('default'):
                        command.run([
                            'ip', 'route', 'add', route, 'dev', self.config['bridge_iface']
                        ], check=True)

                # Then add default routes
                for route in route_addrs:
                    if route.startswith('default'):
                        command.run([
                            'ip', 'route', 'add', route, 'dev', self.config['bridge_iface']
                        ], check=True)

                print(f"{self.config['bridge_iface']} created.")
            return True
        except (subprocess.CalledProcessError, IOError) as e:
            raise f"Failed to set up bridge: {str(e)}"


netservice = NetServices()
