import os
import re
import sys
import time
import subprocess
from ap_utils.colors import fg
from ap_utils.command import command
from ap_utils.config import config_manager
from .netmanager import netmanager
from .shared import shared
import shutil
from .hostapd_manager import hostapdmanager


class NetServices:
    def __init__(self):
        self.config = config_manager.get_config
        self.base_dir = self.config["base_dir"]
        self.proc_dir = self.config["proc_dir"]
        self.conf_dir = self.config.get("conf_dir", config_manager.__bconfdir__)
        self.subnet = self.config["ip_range"]
        self.dhcp_range = self.get_dhcp_range()

    def __enter__(self):
        self.config = config_manager.get_config

    def configure(self):
        print("Configuring services ...")
        self.configure_hostapd()
        self.update_global_hostapd()

        # Configure dnsmasq if not using bridge and not disabled
        if self.config.get("share_method") != "bridge" and not self.config.get(
            "no_dnsmasq", False
        ):
            self.configure_dnsmasq()

    def start(self):
        self.enable_internet_sharing()
        self.start_dhcp_dns()
        # self.start_hostapd()

    def get_dhcp_range(self) -> str:
        """Get DHCP range configuration"""
        return f"{self.subnet.split('/')[0].rsplit('.', 1)[0]}.10,{self.subnet.split('/')[0].rsplit('.', 1)[0]}.100,255.255.255.0,12h"

    def configure_hostapd(self):
        """Configure hostapd with all necessary parameters."""
        try:
            print(
                f"Config: {fg.YELLOW}{os.path.join(self.conf_dir, 'hostapd.conf')}{fg.RESET}"
            )

            # Basic hostapd configuration
            config_lines = [
                f"interface={self.config['vwifi_iface']}",
                f"ssid={self.config['ssid']}",
                f"driver={self.config['driver']}",
                f"ctrl_interface={os.path.join(self.conf_dir, 'hostapd_ctrl')}",
                "ctrl_interface_group=0",
                "max_num_sta=100",
                f"ht_capab={self.config['ht_capab']}",  # [HT40][SHORT-GI-20][DSSS_CCK-40]",
                "auth_algs=1",
                f"ap_isolate={int(self.config.get('isolate_clients', False))}",
                "ignore_broadcast_ssid=0",
                "beacon_int=100\n",
            ]

            # Write basic configuration
            print("Write basic configuration")
            with open(os.path.join(self.conf_dir, "hostapd.conf"), "w") as f:
                # Add country code if specified
                if self.config.get("country"):
                    f.write(f"country_code={self.config['country']}\n")
                    f.write("ieee80211d=1\n")
                    f.write("ieee80211h=1\n")

                # Set hardware mode based on frequency band
                freq_band = float(self.config.get("freq_band", 2.4))
                if freq_band == 2.4:
                    # 2.4GHz configuration
                    f.write("hw_mode=g\n")
                    channel = int(self.config.get("channel", 6))
                    supported_channels = self.get_supported_channels()["2.4GHz"]

                    if channel not in supported_channels:
                        channel_new = supported_channels[0]
                        print(
                            f"Warning: Channel {channel} is invalid for 2.4GHz band, using default channel {channel_new}"
                        )
                        channel = channel_new
                    f.write(f"channel={channel}\n")
                else:
                    # 5GHz configuration
                    f.write("hw_mode=a\n")
                    channel = int(self.config.get("channel", 64))

                    # Get supported channels from hardware
                    supported_channels = self.get_supported_channels()["5GHz"]

                    if not supported_channels:
                        print("Error: No valid 5GHz channels supported by hardware")
                        sys.exit(1)

                    if channel not in supported_channels:
                        print(
                            f"Warning: Channel {channel} not supported, using {supported_channels[0]}"
                        )
                        channel = supported_channels[0]

                    f.write(f"channel={channel}\n")

                # Add the rest of your configuration
                for line in config_lines:
                    f.write(f"{line}\n")

                # Add MAC address filtering if configured
                if self.config.get("mac_filter"):
                    f.write(f"macaddr_acl={int(self.config['mac_filter'])}\n")
                    if self.config.get("mac_filter_accept"):
                        f.write(f"accept_mac_file={self.config['mac_filter_accept']}\n")

                # Add WPA/WPA2 configuration if password is set
                if self.config.get("password"):
                    self._configure_wpa_settings(f)

                # Add bridge configuration if needed
                if self.config.get("share_method") == "bridge":
                    f.write(f"bridge={self.config['bridge_iface']}\n")

            return True

        except (IOError, KeyError) as e:
            sys.exit(f"Failed to configure hostapd: {str(e)}")

    def update_global_hostapd(self):
        shutil.copy(os.path.join(self.conf_dir, "hostapd.conf"), "/etc/hostapd/")

    def _configure_wpa_settings(self, f):
        """Configure WPA/WPA2/WPA3 settings in the hostapd configuration file"""
        try:
            # Handle WPA version
            wpa_version = self.config.get("wpa_version", "2")
            if wpa_version == "1+2":
                wpa_version = "2"  # Default to WPA2 for "1+2" setting

            # Determine key type
            wpa_key_type = (
                "passphrase" if not self.config.get("use_psk", False) else "psk"
            )

            if wpa_version == "3":
                # WPA3 Transition Mode configuration
                f.write(f"wpa_{wpa_key_type}={self.config['password']}\n")
                f.write("wpa_key_mgmt=WPA-PSK SAE\n")
                f.write("wpa_pairwise=CCMP\n")
                f.write("rsn_pairwise=CCMP\n")
                f.write("ieee80211w=1\n")  # Enable management frame protection
            else:
                # Standard WPA/WPA2 configuration
                f.write(f"wpa={wpa_version}\n")
                f.write(f"wpa_{wpa_key_type}={self.config['password']}\n")
                f.write("wpa_key_mgmt=WPA-PSK\n")
                f.write("wpa_pairwise=CCMP\n")
                f.write("rsn_pairwise=CCMP\n")

                # Add WPA3 compatibility if requested
                if wpa_version == "2" and self.config.get("wpa3_compatible", False):
                    f.write("wpa_key_mgmt=WPA-PSK SAE\n")
                    f.write("ieee80211w=1\n")

            # Add additional WPA settings if configured
            if self.config.get("wpa_group_rekey"):
                f.write(f"wpa_group_rekey={self.config['wpa_group_rekey']}\n")

            if self.config.get("wpa_ptk_rekey"):
                f.write(f"wpa_ptk_rekey={self.config['wpa_ptk_rekey']}\n")

            if self.config.get("wpa_gmk_rekey"):
                f.write(f"wpa_gmk_rekey={self.config['wpa_gmk_rekey']}\n")

        except KeyError as e:
            print(f"Missing WPA configuration parameter: {str(e)}")
            raise
        except Exception as e:
            print(f"Error configuring WPA settings: {str(e)}")
            raise

    def get_supported_channels(self):
        """Get list of supported channels from hardware using regex parsing"""
        try:
            # Run iw list command and capture output
            result = subprocess.run(
                ["iw", "list"], capture_output=True, text=True, check=True
            )

            # Regex pattern to match frequency and channel information
            pattern = r"\s*\*\s*(\d+\.\d+)\s+MHz\s*\[(\d+)\]"

            supported_channels = {"2.4GHz": set(), "5GHz": set()}

            # Find all matches in the output
            matches = re.findall(pattern, result.stdout)

            for match in matches:
                freq = float(match[0])
                channel = int(match[1])

                # Determine band and validate channel
                if 2400 <= freq <= 2500:  # 2.4GHz band
                    if 1 <= channel <= 14:
                        supported_channels["2.4GHz"].add(channel)
                elif 5000 <= freq <= 6000:  # 5GHz band
                    if channel in [
                        36,
                        40,
                        44,
                        48,
                        52,
                        56,
                        60,
                        64,
                        100,
                        104,
                        108,
                        112,
                        116,
                        120,
                        124,
                        128,
                        132,
                        136,
                        140,
                        149,
                        153,
                        157,
                        161,
                        165,
                    ]:
                        supported_channels["5GHz"].add(channel)

            # Return both bands' channels
            return {
                "2.4GHz": sorted(supported_channels["2.4GHz"]),
                "5GHz": sorted(supported_channels["5GHz"]),
            }

        except subprocess.CalledProcessError as e:
            print(f"Error getting supported channels: {e}")
            return {"2.4GHz": [], "5GHz": []}
        except Exception as e:
            print(f"Error parsing supported channels: {e}")
            return {"2.4GHz": [], "5GHz": []}

    def configure_dnsmasq(self):
        """Configure dnsmasq for DHCP and DNS services."""
        try:
            # Determine dnsmasq version and appropriate bind option
            dnsmasq_ver = subprocess.run(
                ["dnsmasq", "-v"], capture_output=True, text=True, check=True
            ).stdout.strip()

            # Extract version number and compare
            version_match = re.search(r"[0-9]+(\.[0-9]+)*\.[0-9]+", dnsmasq_ver)
            if (
                version_match
                and netmanager.version_cmp(version_match.group(0), "2.63") == 1
            ):
                dnsmasq_bind = "bind-interfaces"
            else:
                dnsmasq_bind = "bind-dynamic"

            # Set DNS server address
            dhcp_dns = self.config.get("dhcp_dns", None)
            if not dhcp_dns:
                dhcp_dns = self.config["gateway"]

            # Write dnsmasq configuration
            with open(os.path.join(self.conf_dir, "dnsmasq.conf"), "w") as f:
                f.write(f"interface={self.config['vwifi_iface']}\n")
                f.write(f"listen-address={self.config['gateway']}\n")
                f.write(f"{dnsmasq_bind}\n")
                f.write(f"dhcp-range={self.dhcp_range}\n")
                # f.write(f"dhcp-option-force=option:router,{self.config['gateway']}\n")
                f.write(
                    f"dhcp-option=3,{self.config.get('gateway', '192.168.100.1')}\n"
                )
                f.write("dhcp-option=6,8.8.8.8,8.8.4.4\n")  # Google for fallback
                f.write("server=8.8.8.8\n")
                f.write("server=8.8.4.4\n")

                # Add MTU option if available
                mtu = shared.get_mtu(self.config["internet_iface"])
                if mtu:
                    f.write(f"dhcp-option-force=option:mtu,{mtu}\n")

                # Disable hosts file if requested
                if not self.config.get("etc_hosts", True):
                    f.write("no-hosts\n")

                # Add additional hosts file if specified
                if self.config.get("addn_hosts"):
                    f.write(f"addn-hosts={self.config['addn_hosts']}\n")

                # Add DHCP hosts if specified
                if self.config.get("dhcp_hosts"):
                    for host in self.config["dhcp_hosts"]:
                        f.write(f"dhcp-host={host}\n")

                # Configure DNS logging if specified
                if self.config.get("dns_logfile"):
                    f.write("log-queries\n")
                    f.write(f"log-facility={self.config['dns_logfile']}\n")

                # Redirect all traffic to localhost if requested
                if self.config.get("share_method") == "none" and self.config.get(
                    "redirect_to_localhost", False
                ):
                    f.write(f"address=/#/{self.config['gateway']}\n")

        except (subprocess.CalledProcessError, IOError, KeyError) as e:
            sys.exit(f"Failed to configure dnsmasq: {str(e)}")

    def dhcp_service_nodns(self):
        return
        # Configure DNS if not disabled
        dns_port = self.config.get("dns_port", 5353)

        # Set up iptables rules for DNS
        try:
            # Allow TCP DNS traffic
            subprocess.run(
                [
                    "iptables",
                    "-w",
                    "-I",
                    "INPUT",
                    "-p",
                    "tcp",
                    "-m",
                    "tcp",
                    "--dport",
                    str(dns_port),
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # Allow UDP DNS traffic
            subprocess.run(
                [
                    "iptables",
                    "-w",
                    "-I",
                    "INPUT",
                    "-p",
                    "udp",
                    "-m",
                    "udp",
                    "--dport",
                    str(dns_port),
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # Redirect TCP DNS traffic to our port
            gateway_network = f"{'.'.join(self.config['gateway'].split('.')[:3])}.0/24"
            subprocess.run(
                [
                    "iptables",
                    "-w",
                    "-t",
                    "nat",
                    "-I",
                    "PREROUTING",
                    "-s",
                    gateway_network,
                    "-d",
                    self.config["gateway"],
                    "-p",
                    "tcp",
                    "-m",
                    "tcp",
                    "--dport",
                    "53",
                    "-j",
                    "REDIRECT",
                    "--to-ports",
                    str(dns_port),
                ],
                check=True,
            )

            # Redirect UDP DNS traffic to our port
            subprocess.run(
                [
                    "iptables",
                    "-w",
                    "-t",
                    "nat",
                    "-I",
                    "PREROUTING",
                    "-s",
                    gateway_network,
                    "-d",
                    self.config["gateway"],
                    "-p",
                    "udp",
                    "-m",
                    "udp",
                    "--dport",
                    "53",
                    "-j",
                    "REDIRECT",
                    "--to-ports",
                    str(dns_port),
                ],
                check=True,
            )

        except subprocess.CalledProcessError as e:
            sys.exit(f"Failed to set up iptables rules for DNS: {str(e)}")

    def dhcp_service_nodnsmasq(self):
        try:
            # Allow DHCP traffic
            command.run(
                [
                    "iptables",
                    "-w",
                    "-I",
                    "INPUT",
                    "-p",
                    "udp",
                    "-m",
                    "udp",
                    "--dport",
                    "67",
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # Handle AppArmor restrictions
            complain_cmd = None
            try:
                # Check for complain command
                result = subprocess.run(
                    ["command", "-v", "complain"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                complain_cmd = result.stdout.strip()
            except subprocess.CalledProcessError:
                try:
                    # Check for aa-complain command
                    result = subprocess.run(
                        ["command", "-v", "aa-complain"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    complain_cmd = result.stdout.strip()
                except subprocess.CalledProcessError:
                    pass
            except Exception:
                pass

            if complain_cmd:
                command.run([complain_cmd, "dnsmasq"], check=True)

            # Set umask and start dnsmasq
            old_umask = os.umask(0o033)
            try:
                # Start dnsmasq if not running
                # TODO: kill dnsmasq and continue
                if shared.is_dnsmasq_running():
                    shared.kill_dnsmasq()

                print("Starting dnsmasq ..")
                result = subprocess.run(
                    [
                        "dnsmasq",
                        "-C",
                        os.path.join(self.conf_dir, "dnsmasq.conf"),
                        "-x",
                        os.path.join(self.conf_dir, "dnsmasq.pid"),
                        "-l",
                        os.path.join(self.conf_dir, "dnsmasq.leases"),
                        "-p",
                        str(self.config.get("dns_port", 5353)),
                    ],
                    check=True,
                )
                if result.returncode == 0:
                    print("DNSMAQ started OK")
                else:
                    print("Failed to start dnsmasq:", result.stderr or result.stdout)
            except Exception as e:
                print(e)
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
        pid_file = os.path.join(self.conf_dir, "dnsmasq.pid")
        if os.path.exists(pid_file):
            with open(pid_file, "r") as f:
                pid = f.read()
            return pid
        return

    def start_hostapd(self):
        return hostapdmanager.start()
        """Start hostapd with proper error handling and output buffering."""
        # Check if stdbuf is available for unbuffered output
        stdbuf_path = None
        try:
            result = subprocess.run(
                ["which", "stdbuf"], capture_output=True, text=True, check=True
            )
            stdbuf_path = result.stdout.strip()
        except subprocess.CalledProcessError:
            stdbuf_path = None

        # Check if hostapd is already running
        if shared.is_hostapd_running():
            print("Hostapd is already running")
            # return True

        # Check if the interface is already configured
        if shared.is_interface_configured(self.config["vwifi_iface"]):
            print("Interface is already configured, restarting hostapd")
            if not self.restart_hostapd():
                return False

        # Build the hostapd command
        hostapd_cmd = []
        if stdbuf_path:
            hostapd_cmd.extend([stdbuf_path, "-oL"])

        hostapd_cmd.extend(
            [
                self.config["hostapd_path"],
                *self.config.get("hostapd_debug_args", []),
                os.path.join(self.conf_dir, "hostapd.conf"),
            ]
        )
        debug_map = {
            1: "-d",
            2: "-dd",
        }
        debug_level = self.config.get("hostapd_debug", None)

        pid_file = os.path.join(self.proc_dir, "hostapd.pid")

        if self.config.get("daemon", False):
            hostapd_cmd.append("-B")
            if self.config["pidfile"]:
                pid_file = self.config["pidfile"]
                # Create the file
                with open(self.config["pidfile"], "w") as f:
                    f.write("")
                hostapd_cmd.extend(["-P", pid_file])

        if debug_level and debug_level > 0:
            hostapd_cmd.append(debug_map[debug_level])

        hostapd_cmd.extend(["&disown", "&"]) if self.config.get(
            "daemon", False
        ) else None

        # print("HOSTAPD cmd:", hostapd_cmd)
        # Start hostapd in the background
        try:
            # Use Popen to start the process
            self.hostapd_process = subprocess.run(
                hostapd_cmd,
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                start_new_session=True,
                text=True,
            )

            # Save the PID
            self.hostapd_pid = shared.get_hostapd_pid(pid_file)

            print(f"HOSTAPD PID:{fg.CYAN}{self.hostapd_pid}{fg.RESET}")

            # Wait a moment to check if hostapd started successfully
            # Check if the process is still running
            """
            if self.hostapd_process.stdout is not None:
                # Process has terminated, read error output
                stderr_output = self.hostapd_process.stderr
                stdout_output = self.hostapd_process.stdout
                error_msg = stderr_output or stdout_output

                print(f"Error: {fg.FRED}{error_msg}{fg.RESET}")

                print(f"{fg.RED}Hostapd failed to start{fg.RESET}")
                return False

            """
            # Success - hostapd is running in background
            print(f"{fg.GREEN}Hostapd started successfully{fg.RESET}")
            return True

        except Exception as e:
            print(f"Error starting hostapd: {str(e)}")
            return False

    def start_dhcp_dns(self):
        """Start DHCP and DNS services with proper error handling."""
        if self.config["share_method"] != "bridge":
            if not self.config.get("no_dns", False):
                self.dhcp_service_nodns()
            # Start dnsmasq if not disabled
            if not self.config.get("no_dnsmasq", False):
                self.dhcp_service_nodnsmasq()

    def enable_internet_sharing(self):
        """Enable Internet sharing using the specified method."""
        if self.config["share_method"] != "none":
            print(f"Sharing Internet using method: {self.config['share_method']}")

            if self.config["share_method"] == "nat":
                self.nat_sharing()

            elif self.config["share_method"] == "bridge":
                self.bridge_sharing()
        else:
            print("No Internet sharing")

    def nat_sharing(self):
        try:
            # Set up NAT rules
            gateway_network = f"{'.'.join(self.config['gateway'].split('.')[:3])}.0/24"

            # Masquerade traffic from the WiFi network
            command.run(
                [
                    "iptables",
                    "-w",
                    "-t",
                    "nat",
                    "-I",
                    "POSTROUTING",
                    "-s",
                    gateway_network,
                    "!",
                    "-o",
                    self.config["wifi_iface"],
                    "-j",
                    "MASQUERADE",
                ],
                check=True,
            )

            # Allow forwarding from WiFi to internet
            command.run(
                [
                    "iptables",
                    "-w",
                    "-I",
                    "FORWARD",
                    "-i",
                    self.config["wifi_iface"],
                    "-s",
                    gateway_network,
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # Allow forwarding from internet to WiFi
            command.run(
                [
                    "iptables",
                    "-w",
                    "-I",
                    "FORWARD",
                    "-i",
                    self.config["internet_iface"],
                    "-d",
                    gateway_network,
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            iface_file = (
                f"/proc/sys/net/ipv4/conf/{self.config['internet_iface']}/forwarding"
            )
            if not os.path.exists(iface_file):
                print("Choose a different internet interface")

            # Enable IP forwarding for the internet interface
            with open(iface_file, "w") as f:
                f.write("1")

            # Enable IP forwarding globally
            with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
                f.write("1")

            # Load nf_nat_pptp module for PPTP support
            command.run(["modprobe", "nf_nat_pptp"], capture_output=True)
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
                with open("/proc/sys/net/bridge/bridge-nf-call-iptables", "w") as f:
                    f.write("0")

            """
            To initialize the bridge interface correctly we need to do the following:

            1) Save the IPs and route table of INTERNET_IFACE
            2) If NetworkManager is running set INTERNET_IFACE as unmanaged
            3) Create BRIDGE_IFACE and attach INTERNET_IFACE to it
            4) Set the previously saved IPs and route table to BRIDGE_IFACE

            We need the above because BRIDGE_IFACE is the master interface from now on
            and it must know where it's connected, otherwise connection is lost.
            """

            if not shared.is_bridge_interface(self.config["internet_iface"]):
                print("Create a bridge interface... ")

                # Save current IP addresses and routes
                ip_output = subprocess.run(
                    ["ip", "addr", "show", self.config["internet_iface"]],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout

                # Extract IP addresses
                ip_addrs = []
                for line in ip_output.splitlines():
                    if "inet " in line:
                        ip_addrs.append(line.strip())

                # Save current routes
                route_output = subprocess.run(
                    ["ip", "route", "show", "dev", self.config["internet_iface"]],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                route_addrs = [
                    r.strip() for r in route_output.splitlines() if r.strip()
                ]

                # Handle NetworkManager if running
                if netmanager.networkmanager_is_running():
                    netmanager.networkmanager_add_unmanaged(
                        self.config["internet_iface"]
                    )
                    netmanager.networkmanager_wait_until_unmanaged(
                        self.config["internet_iface"]
                    )

                try:
                    # Create bridge interface
                    print("Create bridge interface")
                    subprocess.run(
                        [
                            "ip",
                            "link",
                            "add",
                            "name",
                            self.config["bridge_iface"],
                            "type",
                            "bridge",
                        ],
                        check=True,
                    )
                except Exception as e:
                    print(f"E: {fg.RED}{e}{fg.RESET}")

                print("...s")
                command.run(
                    ["ip", "link", "set", "dev", self.config["bridge_iface"], "up"],
                    check=True,
                )

                # Set 0ms forward delay
                with open(
                    f"/sys/class/net/{self.config['bridge_iface']}/bridge/forward_delay",
                    "w",
                ) as f:
                    f.write("0")

                # Attach internet interface to bridge interface
                print("Attach internet interface to bridge interface")
                command.run(
                    [
                        "ip",
                        "link",
                        "set",
                        "dev",
                        self.config["internet_iface"],
                        "promisc",
                        "on",
                    ],
                    check=True,
                )

                command.run(
                    ["ip", "link", "set", "dev", self.config["internet_iface"], "up"],
                    check=True,
                )

                try:
                    result = subprocess.run(
                        [
                            "ip",
                            "link",
                            "set",
                            "dev",
                            self.config["internet_iface"],
                            "master",
                            self.config["bridge_iface"],
                        ],
                        text=True,
                    )
                    if result.returncode != 0:
                        print(f"{fg.FWHITE}{result.stderr or result.stdout}{fg.RESET}")
                except Exception as e:
                    print(f"E: {fg.RED}{e}{fg.RESET}")

                # Flush old IP addresses
                command.run(
                    ["ip", "addr", "flush", self.config["internet_iface"]], check=True
                )

                # Add saved IP addresses to bridge interface
                for addr in ip_addrs:
                    # Clean up the address string
                    clean_addr = (
                        addr.replace("inet ", "")
                        .replace(" secondary", "")
                        .replace(" dynamic", "")
                    )
                    clean_addr = re.sub(r"(\d+)sec", r"\1", clean_addr)
                    clean_addr = clean_addr.replace(
                        f" {self.config['internet_iface']}", ""
                    )

                    command.run(
                        [
                            "ip",
                            "addr",
                            "add",
                            clean_addr,
                            "dev",
                            self.config["bridge_iface"],
                        ],
                        check=True,
                    )

                # Flush old routes
                command.run(
                    ["ip", "route", "flush", "dev", self.config["internet_iface"]],
                    check=True,
                )

                command.run(
                    ["ip", "route", "flush", "dev", self.config["bridge_iface"]],
                    check=True,
                )

                # Add saved routes to bridge interface
                # First add non-default routes
                for route in route_addrs:
                    if not route.startswith("default"):
                        command.run(
                            [
                                "ip",
                                "route",
                                "add",
                                route,
                                "dev",
                                self.config["bridge_iface"],
                            ],
                            check=True,
                        )

                # Then add default routes
                for route in route_addrs:
                    if route.startswith("default"):
                        command.run(
                            [
                                "ip",
                                "route",
                                "add",
                                route,
                                "dev",
                                self.config["bridge_iface"],
                            ],
                            check=True,
                        )

                print(f"{self.config['bridge_iface']} created.")
            return True
        except Exception as e:
            print(f"E: {fg.RED}{e}{fg.RESET}")
        except (subprocess.CalledProcessError, IOError) as e:
            raise f"Failed to set up bridge: {str(e)}"


netservice = NetServices()
