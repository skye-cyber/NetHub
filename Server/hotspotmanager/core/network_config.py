#!/usr/bin/env python3
"""
Network Configuration Module
Handles all network-related operations including NAT, bridge, DNS, and DHCP configuration
"""

import os
import shutil
from ap_utils.command import command


class NetworkConfigurator:
    def __init__(self, ap_manager):
        """Initialize NetworkConfigurator with reference to main AP manager"""
        self.ap_manager = ap_manager
        self.config = ap_manager.config
        self.lock = ap_manager.lock
        self.netmanager = ap_manager.netmanager
        self.clean = ap_manager.clean
        # self.command = ap_manager.command

        # Configuration paths
        self.conf_dir = self.config.get(
            "conf_dir", ap_manager.config_manager.__bconfdir__
        )
        self.proc_dir = self.config["proc_dir"]

    def setup_nat_configuration(self):
        """Setup NAT configuration for internet sharing"""
        try:
            # Enable IP forwarding
            with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
                f.write("1")

            # Setup iptables rules for NAT
            # 1. Add MASQUERADE for internet interface
            command.run(
                [
                    "iptables",
                    "-w",
                    "-t",
                    "nat",
                    "-A",
                    "POSTROUTING",
                    "-o",
                    self.config[
                        "internet_iface"
                    ],  # Changed: use -o (outgoing interface)
                    "-j",
                    "MASQUERADE",
                ],
                check=True,
            )

            # 2. Allow forwarding from hotspot (xap0) to internet (wlan0)
            command.run(
                [
                    "iptables",
                    "-w",
                    "-A",
                    "FORWARD",
                    "-i",
                    self.config["wifi_iface"],  # hotspot interface
                    "-o",
                    self.config["internet_iface"],  # internet interface
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # 3. Allow return traffic from internet to hotspot (RELATED,ESTABLISHED)
            command.run(
                [
                    "iptables",
                    "-w",
                    "-A",
                    "FORWARD",
                    "-i",
                    self.config["internet_iface"],
                    "-o",
                    self.config["wifi_iface"],
                    "-m",
                    "state",
                    "--state",
                    "RELATED,ESTABLISHED",
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # 4. Change FORWARD policy to ACCEPT
            command.run(["iptables", "-w", "-P", "FORWARD", "ACCEPT"], check=True)

            return True

        except Exception as e:
            self.clean.die(f"Failed to setup NAT configuration: {str(e)}")

    def setup_bridge_configuration(self):
        """Setup bridge configuration for internet sharing"""
        try:
            # Create bridge interface if not already a bridge
            if not self.ap_manager.is_bridge_interface(self.config["internet_iface"]):
                # Create bridge
                command.run(
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

                # Bring down interfaces
                command.run(
                    ["ip", "link", "set", "dev", self.config["internet_iface"], "down"],
                    check=True,
                )
                command.run(
                    ["ip", "link", "set", "dev", self.config["bridge_iface"], "down"],
                    check=True,
                )

                # Set interfaces to promiscuous mode
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

                # Add internet interface to bridge
                command.run(
                    [
                        "ip",
                        "link",
                        "set",
                        "dev",
                        self.config["internet_iface"],
                        "master",
                        self.config["bridge_iface"],
                    ],
                    check=True,
                )

                # Bring up interfaces
                command.run(
                    ["ip", "link", "set", "dev", self.config["bridge_iface"], "up"],
                    check=True,
                )
                command.run(
                    ["ip", "link", "set", "dev", self.config["internet_iface"], "up"],
                    check=True,
                )

                # Save original IP addresses
                result = command.run(
                    ["ip", "addr", "show", "dev", self.config["internet_iface"]],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                self.config["ip_addrs"] = []
                for line in result.stdout.split("\n"):
                    if "inet " in line:
                        self.config["ip_addrs"].append(line.strip())

                # Save original routes
                result = command.run(
                    ["ip", "route", "show", "dev", self.config["internet_iface"]],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                self.config["route_addrs"] = []
                for line in result.stdout.split("\n"):
                    if line.strip():
                        self.config["route_addrs"].append(line.strip())

                # Move IP addresses to bridge
                for addr in self.config["ip_addrs"]:
                    addr = (
                        addr.replace("inet", "")
                        .replace("secondary", "")
                        .replace("dynamic", "")
                    )
                    addr = addr.replace(f"{self.config['internet_iface']}", "").strip()
                    command.run(
                        ["ip", "addr", "add", addr, "dev", self.config["bridge_iface"]],
                        check=True,
                    )

                # Add routes to bridge
                for route in self.config["route_addrs"]:
                    if route and not route.startswith("default"):
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

                # Add default routes last
                for route in self.config["route_addrs"]:
                    if route and route.startswith("default"):
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

            return True

        except Exception as e:
            self.clean.die(f"Failed to setup bridge configuration: {str(e)}")

    def configure_dns(self):
        """Configure DNS server for the hotspot"""
        try:
            if self.config["share_method"] == "bridge" and self.config["no_dns"]:
                return True

            # Allow DNS traffic
            command.run(
                [
                    "iptables",
                    "-w",
                    "-A",
                    "INPUT",
                    "-p",
                    "tcp",
                    "-m",
                    "tcp",
                    "--dport",
                    str(self.config["dns_port"]),
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            command.run(
                [
                    "iptables",
                    "-w",
                    "-A",
                    "INPUT",
                    "-p",
                    "udp",
                    "-m",
                    "udp",
                    "--dport",
                    str(self.config["dns_port"]),
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # Setup DNS redirection
            gateway_network = f"{'.'.join(self.config['gateway'].split('.')[:3])}.0/24"

            command.run(
                [
                    "iptables",
                    "-w",
                    "-t",
                    "nat",
                    "-A",
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
                    str(self.config["dns_port"]),
                ],
                check=True,
            )

            command.run(
                [
                    "iptables",
                    "-w",
                    "-t",
                    "nat",
                    "-A",
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
                    str(self.config["dns_port"]),
                ],
                check=True,
            )

            return True

        except Exception as e:
            self.clean.die(f"Failed to configure DNS: {str(e)}")

    def configure_dhcp(self):
        """Configure DHCP server for the hotspot"""
        try:
            if self.config["share_method"] == "bridge":
                return True

            # Allow DHCP traffic
            command.run(
                [
                    "iptables",
                    "-w",
                    "-A",
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

            return True

        except Exception as e:
            self.clean.die(f"Failed to configure DHCP: {str(e)}")

    def setup_internet_sharing(self):
        """Setup internet sharing based on the configured method"""
        try:
            if self.config["share_method"] == "none":
                return True

            if self.config["share_method"] == "nat":
                return self.setup_nat_configuration()

            elif self.config["share_method"] == "bridge":
                return self.setup_bridge_configuration()

            return False

        except Exception as e:
            self.clean.die(f"Failed to setup internet sharing: {str(e)}")

    def cleanup_nat(self):
        """Cleanup NAT configuration"""
        try:
            gateway_network = f"{'.'.join(self.config['gateway'].split('.')[:3])}.0/24"

            # Remove NAT rules
            command.run(
                [
                    "iptables",
                    "-w",
                    "-t",
                    "nat",
                    "-D",
                    "POSTROUTING",
                    "-s",
                    gateway_network,
                    "!",
                    "-o",
                    self.config["wifi_iface"],
                    "-j",
                    "MASQUERADE",
                ],
                check=False,
            )

            command.run(
                [
                    "iptables",
                    "-w",
                    "-D",
                    "FORWARD",
                    "-i",
                    self.config["wifi_iface"],
                    "-s",
                    gateway_network,
                    "-j",
                    "ACCEPT",
                ],
                check=False,
            )

            command.run(
                [
                    "iptables",
                    "-w",
                    "-D",
                    "FORWARD",
                    "-i",
                    self.config["internet_iface"],
                    "-d",
                    gateway_network,
                    "-j",
                    "ACCEPT",
                ],
                check=False,
            )

            return True

        except Exception as e:
            self.clean.die(f"Failed to cleanup NAT: {str(e)}")

    def cleanup_bridge(self):
        """Cleanup bridge configuration"""
        try:
            # Remove bridge configuration if not already a bridge interface
            if not self.ap_manager.is_bridge_interface(self.config["internet_iface"]):
                command.run(
                    ["ip", "link", "set", "dev", self.config["bridge_iface"], "down"],
                    check=False,
                )

                command.run(
                    ["ip", "link", "set", "dev", self.config["internet_iface"], "down"],
                    check=False,
                )

                command.run(
                    [
                        "ip",
                        "link",
                        "set",
                        "dev",
                        self.config["internet_iface"],
                        "promisc",
                        "off",
                    ],
                    check=False,
                )

                command.run(
                    [
                        "ip",
                        "link",
                        "set",
                        "dev",
                        self.config["internet_iface"],
                        "nomaster",
                    ],
                    check=False,
                )

                command.run(
                    [
                        "ip",
                        "link",
                        "delete",
                        self.config["bridge_iface"],
                        "type",
                        "bridge",
                    ],
                    check=False,
                )

                command.run(
                    ["ip", "addr", "flush", self.config["internet_iface"]], check=False
                )

                command.run(
                    ["ip", "link", "set", "dev", self.config["internet_iface"], "up"],
                    check=False,
                )

                self.ap_manager.dealloc_iface(self.config["bridge_iface"])

                # Restore original IP addresses
                for addr in self.config.get("ip_addrs", []):
                    addr = (
                        addr.replace("inet", "")
                        .replace("secondary", "")
                        .replace("dynamic", "")
                    )
                    addr = addr.replace(f"{self.config['internet_iface']}", "").strip()
                    command.run(
                        [
                            "ip",
                            "addr",
                            "add",
                            addr,
                            "dev",
                            self.config["internet_iface"],
                        ],
                        check=False,
                    )

                # Restore original routes
                command.run(
                    ["ip", "route", "flush", "dev", self.config["internet_iface"]],
                    check=False,
                )

                for route in self.config.get("route_addrs", []):
                    if route and not route.startswith("default"):
                        command.run(
                            [
                                "ip",
                                "route",
                                "add",
                                route,
                                "dev",
                                self.config["internet_iface"],
                            ],
                            check=False,
                        )

                # Add default routes last
                for route in self.config.get("route_addrs", []):
                    if route and route.startswith("default"):
                        command.run(
                            [
                                "ip",
                                "route",
                                "add",
                                route,
                                "dev",
                                self.config["internet_iface"],
                            ],
                            check=False,
                        )

                # Remove from NetworkManager unmanaged list if needed
                self.netmanager.networkmanager_rm_unmanaged_if_needed(
                    self.config["internet_iface"]
                )

            return True

        except Exception as e:
            self.clean.die(f"Failed to cleanup bridge: {str(e)}")

    def cleanup_dns(self):
        """Cleanup DNS configuration"""
        try:
            if self.config["share_method"] == "bridge" and self.config["no_dns"]:
                return True

            command.run(
                [
                    "iptables",
                    "-w",
                    "-D",
                    "INPUT",
                    "-p",
                    "tcp",
                    "-m",
                    "tcp",
                    "--dport",
                    str(self.config["dns_port"]),
                    "-j",
                    "ACCEPT",
                ],
                check=False,
            )

            command.run(
                [
                    "iptables",
                    "-w",
                    "-D",
                    "INPUT",
                    "-p",
                    "udp",
                    "-m",
                    "udp",
                    "--dport",
                    str(self.config["dns_port"]),
                    "-j",
                    "ACCEPT",
                ],
                check=False,
            )

            gateway_network = f"{'.'.join(self.config['gateway'].split('.')[:3])}.0/24"

            command.run(
                [
                    "iptables",
                    "-w",
                    "-t",
                    "nat",
                    "-D",
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
                    str(self.config["dns_port"]),
                ],
                check=False,
            )

            command.run(
                [
                    "iptables",
                    "-w",
                    "-t",
                    "nat",
                    "-D",
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
                    str(self.config["dns_port"]),
                ],
                check=False,
            )

            return True

        except Exception as e:
            self.clean.die(f"Failed to cleanup DNS: {str(e)}")

    def cleanup_dhcp(self):
        """Cleanup DHCP configuration"""
        try:
            if self.config["share_method"] != "bridge":
                command.run(
                    [
                        "iptables",
                        "-w",
                        "-D",
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
                    check=False,
                )

            return True

        except Exception as e:
            self.clean.die(f"Failed to cleanup DHCP: {str(e)}")

    def cleanup_interfaces(self):
        """Cleanup network interfaces"""
        try:
            # Cleanup virtual interface if not disabled
            if not self.config["no_virt"] and self.config.get("vwifi_iface"):
                command.run(
                    ["ip", "link", "set", "down", "dev", self.config["vwifi_iface"]],
                    check=False,
                )

                command.run(
                    ["ip", "addr", "flush", self.config["vwifi_iface"]], check=False
                )

                self.netmanager.networkmanager_rm_unmanaged_if_needed(
                    self.config["vwifi_iface"], self.config.get("old_macaddr")
                )

                command.run(
                    ["iw", "dev", self.config["vwifi_iface"], "del"], check=False
                )

                self.ap_manager.dalloc_iface(self.config["vwifi_iface"])
            else:
                # Cleanup main interface
                command.run(
                    ["ip", "link", "set", "down", "dev", self.config["wifi_iface"]],
                    check=False,
                )

                command.run(
                    ["ip", "addr", "flush", self.config["wifi_iface"]], check=False
                )

                if self.config.get("new_macaddr"):
                    command.run(
                        [
                            "ip",
                            "link",
                            "set",
                            "dev",
                            self.config["wifi_iface"],
                            "address",
                            self.config.get("old_macaddr"),
                        ],
                        check=False,
                    )

                self.netmanager.networkmanager_rm_unmanaged_if_needed(
                    self.config["wifi_iface"], self.config.get("old_macaddr")
                )

            return True

        except Exception as e:
            self.clean.die(f"Failed to cleanup interfaces: {str(e)}")

    def restore_forwarding_config(self):
        """Restore original forwarding configuration"""
        try:
            # Check if we're the last instance using this internet interface
            found = False
            for conf_dir in self.list_running_conf():
                nat_internet_iface_path = os.path.join(conf_dir, "nat_internet_iface")
                if os.path.exists(nat_internet_iface_path):
                    with open(nat_internet_iface_path, "r") as f:
                        if f.read().strip() == self.config["internet_iface"]:
                            found = True
                            break

            if not found and self.config["internet_iface"]:
                # Restore original forwarding setting
                forwarding_file = os.path.join(
                    self.conf_dir, f"{self.config['internet_iface']}_forwarding"
                )

                if os.path.exists(forwarding_file):
                    with (
                        open(forwarding_file, "r") as src,
                        open(
                            f"/proc/sys/net/ipv4/conf/{self.config['internet_iface']}/forwarding",
                            "w",
                        ) as dst,
                    ):
                        shutil.copyfileobj(src, dst)
                    os.remove(forwarding_file)

            return True

        except Exception as e:
            self.clean.die(f"Failed to restore forwarding config: {str(e)}")

    def list_running_conf(self) -> list:
        """List all running configuration directories"""
        running_confs = []
        try:
            if os.path.exists(self.conf_dir):
                for item in os.listdir(self.proc_dir):
                    # Skip non-ap_manager files
                    if not item.startswith("ap_manager"):
                        continue

                    # Check if this is a valid running configuration
                    pid_file = item.endswith(
                        ".pid"
                    )  # os.path.join(self.proc_dir, item + '.pid') if item else None
                    # wifi_iface_file = os.path.join(self.conf_dir, item, 'wifi_iface') if item else None

                    if pid_file:  # and wifi_iface_file:
                        # if os.path.exists(pid_file) and os.path.exists(wifi_iface_file):
                        running_confs.append(os.path.join(item))
        except OSError:
            pass

        return running_confs

    def get_running_instances(self) -> list:
        """List all running configuration directories"""
        running_instances = []

        try:
            if os.path.exists(self.proc_dir):
                for item in os.listdir(self.proc_dir):
                    # Skip non-ap_manager files
                    if not any((item.startswith("ap_manager"), item.endswith(".pid"))):
                        continue

                    ipath = os.path.join(self.proc_dir, item)

                    if not os.path.isfile(ipath):
                        continue

                    pid = None
                    with open(ipath, "r") as fr:
                        pid = fr.read()

                    conf = os.path.join(ipath.strip(".pid"), "vwifi_iface")

                    iface = None
                    if os.path.exists(conf):
                        with open(conf, "r") as f:
                            iface = f.read()

                    if not pid or not iface:
                        continue

                    running_instances.append({"pid": pid, "viface": iface})
        except OSError:
            pass

        return running_instances
