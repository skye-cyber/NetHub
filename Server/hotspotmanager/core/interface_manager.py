#!/usr/bin/env python3
"""
Interface Manager Module
Handles all interface-related operations including creation, configuration, and cleanup
"""

import os
import re
import subprocess
import uuid
from ap_utils.colors import fg
from ap_utils.command import command
from ap_utils.copy import cp_n_safe
from .services import netservice
from .shared import shared
from pathlib import Path


class InterfaceManager:
    def __init__(self, ap_manager):
        """Initialize InterfaceManager with reference to main AP manager"""
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

        # Ensure directories exist
        os.makedirs(self.proc_dir, exist_ok=True)
        os.makedirs(self.conf_dir, exist_ok=True)

        self.virt_diems = "Maybe your WiFi adapter does not fully support virtual interfaces. Try again with --no-virt."

    def initialize_access_point(self):
        """Initialize the access point with proper configuration"""
        try:
            # Lock mutex for thread safety
            self.lock.mutex_lock()

            # Create configuration directory if it doesn't exist
            os.makedirs(self.config["conf_dir"], exist_ok=True)

            # Write PID file
            _uuid_ = uuid.uuid4()
            pidf_name = f"ap_manager-{str(_uuid_)[:6]}.pid"
            pid_file = os.path.join(self.proc_dir, pidf_name)

            with open(pid_file, "w") as f:
                f.write(str(os.getpid()))

            # Set proper permissions for the PID file
            os.chmod(pid_file, 0o444)

            # Write internet interface information
            nat_internet_file = os.path.join(self.conf_dir, "nat_internet_iface")
            with open(nat_internet_file, "w") as f:
                f.write(self.config["internet_iface"])

            # Save forwarding configuration
            forwarding_src = (
                f"/proc/sys/net/ipv4/conf/{self.config['internet_iface']}/forwarding"
            )
            forwarding_dst = os.path.join(
                self.conf_dir, f"{self.config['internet_iface']}_forwarding"
            )
            cp_n_safe(forwarding_src, forwarding_dst)

            # Save IP forwarding configuration
            ip_forward_src = "/proc/sys/net/ipv4/ip_forward"
            ip_forward_dst = os.path.join(self.conf_dir, "ip_forward")
            cp_n_safe(ip_forward_src, ip_forward_dst)

            # Save bridge configuration if available
            if os.path.exists("/proc/sys/net/bridge/bridge-nf-call-iptables"):
                bridge_src = "/proc/sys/net/bridge/bridge-nf-call-iptables"
                bridge_dst = os.path.join(self.conf_dir, "bridge-nf-call-iptables")
                cp_n_safe(bridge_src, bridge_dst)

            # Unlock mutex
            self.lock.mutex_unlock()

            # Create virtual interface first (before setup_interface tries to use it)
            self.create_virtual_interface()

            self.setup_interface()

            self.update_configuration()

            netservice.configure()

            # Start services [hostapd, dnsmasq, dns, internet sharing]
            netservice.start()
            self.save_iface_info(pid_file)

            self.set_country()

            return self.start_apmanager_service()
        except Exception as e:
            self.clean.die(f"AP Initialization failed: {str(e)}")

    def stop_accesspoint(self) -> bool:
        shared.stop_service("hostapd")
        return shared.stop_service("ap_manger")

    def start_apmanager_service(self) -> bool:
        # Make interface unmanaged if needed
        try:
            pass  # self.netmanager.networkmanager_rm_unmanaged(self.config['vwifi_iface'])
        except Exception as e:
            self.clean.die(f"Failed to make interface unmanaged: {str(e)}")

        finally:
            try:
                # shared.kill_hostapd()
                # shared.start_service("dnsmasq", restart=True)
                # shared.start_dnsmasq((Path(self.conf_dir) / "dnsmasq.conf").as_posix())
                return shared.start_service("ap_manager", restart=True)

                # netservice.start_hostapd()
            except Exception as e:
                print(f"Failed to start ap manager service {str(e)}")
                return False

    def set_country(self) -> bool:
        # Set country code if needed
        if self.config["country"] and self.ap_manager.use_iwconfig:
            try:
                subprocess.run(["iw", "reg", "set", self.config["country"]], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to set country code: {str(e)}")
                return False
        return True

    def save_iface_info(self, pid_file) -> bool:
        # Lock mutex for writing interface information
        self.lock.mutex_lock()
        try:
            iface_dir = os.path.join(self.conf_dir, pid_file.strip(".pid"))
            os.makedirs(iface_dir, exist_ok=True)

            wifi_iface_file = os.path.join(iface_dir, "vwifi_iface")
            with open(wifi_iface_file, "w") as f:
                f.write(self.config["vwifi_iface"])
            os.chmod(wifi_iface_file, 0o444)
            return True
        except Exception:
            return False
        finally:
            self.lock.mutex_unlock()

    def update_configuration(self) -> bool:
        # Update and save configuration
        try:
            self.ap_manager.config_manager._dict_update(
                self.ap_manager.config_manager.get_config, self.config
            )
            self.ap_manager.config_manager.save_config()
            return True
        except Exception as e:
            print(f"Failed to update configuration: {str(e)}")
            return False

    def setup_interface(self):
        try:
            # Determine bridge interface
            if self.config["share_method"] == "bridge":
                if self.is_bridge_interface(self.config["internet_iface"]):
                    self.config["bridge_iface"] = self.config["internet_iface"]
                # else:
                # self.config['bridge_iface'] = self.alloc_new_iface('xbr')

            # Setup frequency and channel (check physical interface if using virtual)
            self.setup_frequency_and_channel()

            # Handle virtual interface configuration
            if self.config["no_virt"]:
                # When no_virt is set, we use the physical interface as the access point
                self.config["vwifi_iface"] = self.config[
                    "vwifi_iface"
                ] or self.alloc_new_iface("xap")

                # Set virtual interface as unmanaged in NetworkManager if possible
                if (
                    self.netmanager.networkmanager_is_running()
                    and self.netmanager.NM_OLDER_VERSION == 0
                ):
                    print(
                        f"Network Manager found, set {self.config['vwifi_iface']} as unmanaged device... "
                    )
                    try:
                        self.netmanager.networkmanager_add_unmanaged(
                            self.config["vwifi_iface"]
                        )
                        print("DONE")
                    except Exception as e:
                        self.clean.die(
                            f"Failed to set interface as unmanaged: {str(e)}"
                        )
        except Exception as e:
            self.clean.die(f"Failed setup interface: {str(e)}")

    def setup_frequency_and_channel(self):
        """Set correct frequency and channel for the WiFi interface"""
        # Check if we're using virtual interface or physical interface
        check_iface = (
            self.config["vwifi_iface"]
            if self.config.get("no_virt", False)
            else self.config["wifi_iface"]
        )

        if self.is_wifi_connected(check_iface):
            if not self.config["freq_band"]:
                wifi_iface_freq = self.netmanager._get_interface_freq_(check_iface)
                wifi_iface_channel = self.ieee80211_frequency_to_channel(
                    wifi_iface_freq
                )

                print(
                    f"{check_iface} is already associated with channel "
                    f"{wifi_iface_channel} ({wifi_iface_freq} MHz)"
                )

                self.config.update({"freq_band": 5}) if self.is_5ghz_frequency(
                    wifi_iface_freq
                ) else self.config.update({"freq_band": 2.4})

                if wifi_iface_channel != wifi_iface_channel:
                    if self._get_channels_() >= 2 and self.can_transmit_to_channel(
                        check_iface, self.config["channel"]
                    ):
                        print("multiple channels supported")
                    else:
                        # Fallback to currently connected channel
                        print(
                            f"multiple channels not supported, fallback to channel: {wifi_iface_channel}"
                        )
                        self.config.update({"channel": wifi_iface_channel})
                        if self.can_transmit_to_channel(
                            check_iface, self.config["channel"]
                        ):
                            print(
                                f"Transmitting to channel {self.config['channel']}..."
                            )
                        else:
                            self.clean.die(
                                f"Your adapter can not transmit to channel {self.config['channel']}, "
                                f"frequency band {self.config['freq_band']}GHz."
                            )
                else:
                    print(f"channel: {self.config['channel']}")
            else:
                print(
                    f"Custom frequency band set to {self.config['freq_band']}Ghz and channel {self.config['channel']}"
                )

    def create_virtual_interface(self):
        """Create a virtual WiFi interface with proper configuration"""
        try:
            if not self.interface_exists(self.config["vwifi_iface"]):
                print("Creating a virtual WiFi interface... ", end="")
                # Actually create the virtual interface using iw command
                command.run(
                    [
                        "iw",
                        "dev",
                        self.config["wifi_iface"],
                        "interface",
                        "add",
                        self.config["vwifi_iface"],
                        "type",
                        "__ap",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    force_return=True,
                )
            else:
                print("Virtual wifi interface exist: skipping ...")

            print(f"\n{fg.YELLOW}Hostapd{fg.RESET} already configured!")

            print(f"\n{fg.LWHITE}{fg.DWHITE}Interface\tStatus{fg.RESET}")
            print(
                f"\n{fg.BLUE}{self.config['vwifi_iface']}\t\t{fg.BGREEN}Ready{fg.RESET}\n"
            )

            # Wait for NetworkManager to recognize the interface if needed
            if (
                self.netmanager.networkmanager_is_running()
                and self.netmanager.NM_OLDER_VERSION == 0
            ):
                self.make_interface_unmanaged()

            # Handle MAC address configuration
            new_mac = self.config.get("mac")
            all_macs = self.get_all_mac_addresses()

            # If no new MAC specified or it's already in use, generate a new one
            if not new_mac or new_mac in all_macs:
                new_mac = self.get_new_mac_address(self.config["vwifi_iface"])
                print(f"Generated ne mac: {fg.MAGENTA}{new_mac}{fg.RESET}")
                if not new_mac:
                    self.clean.die("Failed to generate new MAC address")
                self.config["mac"] = new_mac

            # Update configuration with new interface and MAC
            # self.config['vwifi_iface'] = self.config['vwifi_iface']

        except Exception as e:
            self.clean.die(
                f"{fg.RED}Error during virtual interface creation: "
                f"{fg.LRED}{str(e)}{fg.RESET}"
            )

    def make_interface_unmanaged(self):
        """Make the WiFi interface unmanaged by NetworkManager"""
        if self.netmanager.networkmanager_exists():
            if not self.netmanager.networkmanager_iface_is_unmanaged(
                self.config["vwifi_iface"]
            ):
                print(
                    f"Network Manager found, set {self.config['vwifi_iface']} as unmanaged device... "
                )
                unmanaged = self.netmanager.networkmanager_add_unmanaged(
                    self.config["vwifi_iface"]
                )
                print(
                    f"{fg.BYELLOW}{self.config['vwifi_iface']}{fg.RESET} State: {fg.GREEN}{'unmanaged' if unmanaged else 'managed'}{fg.RESET}"
                )

                if self.netmanager.networkmanager_is_running():
                    if not self.netmanager.networkmanager_wait_until_unmanaged(
                        self.config["vwifi_iface"]
                    ):
                        self.clean.die("Failed to wait for interface to be unmanaged")
                    print(" - DONE")
            else:
                print(
                    f"Interface {self.config['vwifi_iface']} is already UNMANAGED. Skip..."
                )
        else:
            print("NetworkMnager not found")

    def initialize_wifi_interface(self):
        """Initialize the WiFi interface with proper configuration"""
        print(
            f"Initialize wifi: {fg.YELLOW}{self.config['vwifi_iface']}{fg.RESET} on {fg.BWHITE}{self.config['internet_iface']}{fg.RESET}"
        )

        try:
            print("Flush addresses")
            # Bring interface down and flush addresses
            command.run(
                ["ip", "link", "set", "down", "dev", self.config["vwifi_iface"]],
                check=True,
            )

            command.run(["ip", "addr", "flush", self.config["vwifi_iface"]], check=True)

            # Set MAC address if virtualization is enabled and MAC is specified
            if self.config.get("mac") and 0 > 1:
                self.netmanager.wifi_switch(state="off")
                command.run(
                    [
                        "ip",
                        "link",
                        "set",
                        "dev",
                        self.config["vwifi_iface"],
                        "address",
                        self.config["mac"],
                    ],
                    check=True,
                )
                self.netmanager.wifi_switch(state="on")

            # Configure interface
            print(
                f"Configure interface for {self.config['share_method']} sharing method"
            )
            if self.config.get("share_method", "none") != "bridge":
                # Bring interface up
                def bring_interface_up():
                    self.netmanager.wifi_switch(state="off")
                    self.netmanager.rfkill_off()
                    result = command.run(
                        ["ip", "link", "set", "up", "dev", self.config["vwifi_iface"]],
                        check=True,
                        force_return=True,
                    )
                    self.netmanager.wifi_switch(state="off")
                    return result

                result = bring_interface_up()
                if (
                    not result
                    or isinstance(result, dict)
                    and result["status"] == "error"
                ):
                    command.run(["sudo", "rfkill", "unblock", "all"], check=True)
                    bring_interface_up()

                # **FIXED**: Use a different IP for the AP interface
                # Extract network from gateway, use .1 for AP interface
                gateway = self.config["gateway"]
                gateway_parts = gateway.split(".")
                ap_ip = f"{gateway_parts[0]}.{gateway_parts[1]}.{gateway_parts[2]}.1"
                broadcast = (
                    f"{gateway_parts[0]}.{gateway_parts[1]}.{gateway_parts[2]}.255"
                )

                print(f" - Set AP IP address: {ap_ip}/24 (broadcast: {broadcast})\n")
                print(f" - Gateway for clients will be: {gateway}\n")

                command.run(
                    [
                        "ip",
                        "addr",
                        "add",
                        f"{ap_ip}/24",
                        "broadcast",
                        broadcast,
                        "dev",
                        self.config["vwifi_iface"],
                    ],
                    check=True,
                )

            return True

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to initialize WiFi interface: {str(e)}"
            if hasattr(self, "virt_diems"):
                error_msg += f"\n{self.virt_diems}"
            self.clean.die(error_msg)

    def x__initialize_wifi_interface(self):
        """Initialize the WiFi interface with proper configuration"""
        print(
            f"Initialize wifi: {fg.YELLOW}{self.config['vwifi_iface']}{fg.RESET} on {fg.BWHITE}{self.config['internet_iface']}{fg.RESET}"
        )

        try:
            print("Flush addresses")
            # Bring interface down and flush addresses
            command.run(
                ["ip", "link", "set", "down", "dev", self.config["vwifi_iface"]],
                check=True,
            )

            command.run(["ip", "addr", "flush", self.config["vwifi_iface"]], check=True)

            # Set MAC address if virtualization is enabled and MAC is specified
            # if not self.config.get('no_virt', False) and
            if self.config.get("mac"):
                self.netmanager.wifi_switch(state="off")
                command.run(
                    [
                        "ip",
                        "link",
                        "set",
                        "dev",
                        self.config["vwifi_iface"],
                        "address",
                        self.config["mac"],
                    ],
                    check=True,
                )
                self.netmanager.wifi_switch(state="on")

            # Set MAC address if virtualization is disabled and MAC is specified
            """
            if self.config.get('no_virt', False) and self.config.get('mac'):
                command.run([
                    'ip', 'link', 'set', 'dev', self.config['vwifi_iface'],
                    'address', self.config['mac']
                ], check=True)
            """

            # Configure interface for non-bridge sharing method
            print("Configure interface for non-bridge sharing method")
            if self.config.get("share_method", "none") != "bridge":
                # Bring interface up
                # print(" - Bring interface up\n")

                def bring_interface_up():
                    return command.run(
                        ["ip", "link", "set", "up", "dev", self.config["vwifi_iface"]],
                        check=True,
                        force_return=True,
                    )

                result = True  # bring_interface_up()
                if (
                    not result
                    or isinstance(result, dict)
                    and result["status"] == "error"
                ):
                    command.run(["sudo", "rfkill", "unblock", "all"], check=True)
                    bring_interface_up()

                # Set IP address and broadcast
                print(" - Set IP address and broadcast\n")
                gateway = self.config["gateway"]
                ip_range = self.config["ip_range"]
                broadcast = f"{'.'.join(gateway.split('.')[:3])}.255"

                command.run(
                    [
                        "ip",
                        "addr",
                        "add",
                        ip_range,
                        "broadcast",
                        broadcast,
                        "dev",
                        self.config["vwifi_iface"],
                    ],
                    check=True,
                )

            return True

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to initialize WiFi interface: {str(e)}"
            if hasattr(self, "virt_diems"):
                error_msg += f"\n{self.virt_diems}"
            self.clean.die(error_msg)

    # Utility methods from original ap_manager.py
    def _get_channels_(self) -> bool:
        """Check if adapter supports multiple channels"""
        adapter_info = self.get_adapter_info()
        return bool(re.search(r"channels\s<=\s2", adapter_info))

    def ieee80211_frequency_to_channel(self, _freq=None):
        """Convert frequency to channel number (taken from iw/util.c)"""
        _freq = _freq if _freq else self.config["freq_band"]
        freq = int(_freq.split(".")[0])

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
        return bool(re.match(r"^(49[0-9]{2})|(5[0-9]{3})(\.0+)?$", str(freq)))

    def is_wifi_connected(self, iface=None):
        """Check if WiFi interface is connected"""
        iface = iface if iface else self.config["vwifi_iface"]

        if not self.ap_manager.use_iwconfig:
            try:
                result = subprocess.run(
                    ["iw", "dev", iface, "link"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return "Connected to" in result.stdout
            except subprocess.CalledProcessError:
                return False
        else:
            try:
                result = subprocess.run(
                    ["iwconfig", iface], capture_output=True, text=True, check=True
                )
                return bool(re.search(r"Access Point: [0-9a-fA-F]{2}:", result.stdout))
            except subprocess.CalledProcessError:
                return False

    def is_mac_address(self, mac=None):
        """Check if string is a valid MAC address"""
        mac = mac if mac else self.config["mac"]
        if not mac:
            return False
        return bool(re.match(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$", mac))

    def is_unicast_mac_address(self, mac=None):
        """Check if MAC address is unicast"""
        mac = mac if mac else self.config["mac"]
        if not self.is_mac_address(mac):
            return False
        first_byte = int(mac.split(":")[0], 16)
        return first_byte % 2 == 0

    def is_interface(self, iface=None) -> bool:
        return shared.is_interface(iface)

    def get_mac_address(self, iface=None):
        """Get MAC address of an interface"""
        iface = iface if iface else self.config["vwifi_iface"]
        if not self.is_interface(iface):
            return None
        try:
            with open(f"/sys/class/net/{iface}/address", "r") as f:
                return f.read().strip()
        except IOError:
            return None

    def get_mtu(self, iface=None) -> int:
        """Get MTU of an interface"""
        iface = iface if iface else self.config["vwifi_iface"]
        if not self.is_interface(iface):
            return None
        try:
            with open(f"/sys/class/net/{iface}/mtu", "r") as f:
                return int(f.read().strip())
        except (IOError, ValueError):
            return None

    def alloc_new_iface(self, prefix=None):
        """Allocate a new interface name"""
        prefix = prefix if prefix else self.config["vwifi_iface"]
        # if interface is say wlan0 use wlan as the prefix
        if prefix[-1].isnumeric():
            prefix = prefix[:-1]
        i = 0
        self.lock.mutex_lock()
        try:
            while i > 100:
                iface_name = f"{prefix}{i}"
                if not self.is_interface(iface_name) and not os.path.exists(
                    f"{self.conf_dir}/ifaces/{iface_name}"
                ):
                    os.makedirs(f"{self.conf_dir}/ifaces", exist_ok=True)
                    with open(f"{self.conf_dir}/ifaces/{iface_name}", "w"):
                        pass  # Just create the file
                    self.lock.mutex_unlock()
                    return iface_name
                i += 1
        finally:
            self.lock.mutex_unlock()

    def dealloc_iface(self, iface=None):
        """Deallocate a new interface name"""
        prefix = iface if iface else self.config["vwifi_iface"]
        # if interface is say wlan0 use wlan as the prefix
        if prefix[-1].isnumeric():
            prefix = prefix[:-1]

        self.lock.mutex_lock()

        try:
            for i in range(5):
                iface_name = f"{prefix}{i}"
                if all(
                    (
                        self.is_interface(iface_name),
                        os.path.exists(f"{self.conf_dir}/ifaces/{iface_name}"),
                    )
                ):
                    os.remove(f"{self.conf_dir}/ifaces/{iface_name}")
                    self.lock.mutex_unlock()
                    return iface_name
                i += 1
        finally:
            self.lock.mutex_unlock()

    def can_transmit_to_channel(self, iface=None, channel=None):
        """Check if interface can transmit to specified channel"""
        iface = iface if iface else self.config["vwifi_iface"]
        channel = channel if channel else self.config["channel"]

        if not self.ap_manager.use_iwconfig:
            # Determine frequency band pattern
            if self.config["freq_band"] == 2.4:
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
            iwlist_output = command.run(f"iwlist {iface} channel")
            pattern = rf"Channel\s+{formatted_channel}\s?:"
            channel_info = re.search(pattern, iwlist_output)

            return bool(channel_info)

    def can_be_ap(self, iface=None):
        """Check if interface can be an access point"""
        iface = iface if iface else self.config["vwifi_iface"]
        if self.ap_manager.use_iwconfig:
            return True

        adapter_info = self.get_adapter_info(iface)
        match = re.search(r"#{\s*AP\s?}?", adapter_info)
        return bool(match)

    def can_be_sta_and_ap(self, iface=None):
        """Check if interface can be both station and access point"""
        iface = iface if iface else self.config["vwifi_iface"]

        if self.get_adapter_kernel_module(iface) == "brcmfmac":
            warning = """WARN: brmfmac driver doesn't work properly with virtual interfaces and
            it can cause kernel panic. For this reason we disallow virtual
            interfaces for your adapter.
            For more info: https://github.com/skye-cyber/ap_manager/issues/203"""
            print(warning)
            return False

        # Check if adapter supports both STA and AP modes
        adapter_info = self.get_adapter_info()
        if re.search(
            r"#{\s*managed\s*}\s*<?=?\s*[1-9]?\s*,?\s*#{\s*AP,\s*", adapter_info
        ) or re.search(r"{\s*AP\s*managed\s*}", adapter_info):
            return True

        return False

    def get_adapter_kernel_module(self, _iface=None) -> str:
        """Get the kernel module for the WiFi adapter"""
        iface = _iface if _iface else self.config["vwifi_iface"]
        module_path = os.path.realpath(f"/sys/class/net/{iface}/device/driver/module")
        module_name = os.path.basename(module_path)
        return module_name

    def get_adapter_info(self, iface=None) -> str:
        """Get detailed information about the WiFi adapter"""
        iface = iface if iface else self.config["wifi_iface"]

        PHY = self.get_phy_device(iface)
        if not PHY:
            return None

        result = command.run(["iw", "phy", PHY, "info"], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else None

    def get_phy_device(self, iface=None) -> str:
        """Get the PHY device for the WiFi interface"""
        t_iface = iface if iface else self.config["wifi_iface"]
        c_dir = "/sys/class/ieee80211/"

        for x in os.listdir(c_dir):
            if x == t_iface or t_iface in x:  # check partial match
                return x
            elif os.path.exists(f"{c_dir}/{x}/device/net/{t_iface}"):
                return x
            elif os.path.exists(f"{c_dir}/{x}/device/net:{t_iface}"):
                return x

        print("Failed to get phy interface")
        return None

    def __get_phy_device__(self, iface=None) -> str:
        t_iface = iface if iface else self.config["wifi_iface"]
        c_dir = "/sys/class/ieee80211/"

        # Check if the interface exists directly
        if t_iface in os.listdir(c_dir):
            return t_iface

        # Check for partial matches
        for x in os.listdir(c_dir):
            if t_iface in x:
                return x

            # Check for net device links
            net_path = f"{c_dir}/{x}/device/net/{t_iface}"
            if os.path.exists(net_path):
                return x

            # Check for alternative net device path
            net_path = f"{c_dir}/{x}/device/net:{t_iface}"
            if os.path.exists(net_path):
                return x

        # Check if the physical interface exists but isn't linked
        if "phy0" in os.listdir(c_dir):
            return "phy0"

        print("Failed to get phy interface - no wireless devices found")
        return None

    def is_bridge_interface(self, iface=None):
        return shared.is_bridge_interface(iface)

    def is_wifi_interface(self, _iface=None):
        """Check if interface is a WiFi interface"""
        iface = _iface if _iface else self.config["wifi_iface"]

        try:
            # Check if 'iw' command exists and works
            if (
                subprocess.run(
                    ["which", "iw"], check=True, capture_output=True
                ).returncode
                == 0
            ):
                result = subprocess.run(
                    ["iw", "dev", iface, "info"], capture_output=True
                )
                if result.returncode == 0:
                    return True

            # Check if 'iwconfig' command exists and works
            if (
                subprocess.run(
                    ["which", "iwconfig"], check=True, capture_output=True
                ).returncode
                == 0
            ):
                result = subprocess.run(["iwconfig", iface], capture_output=True)
                if result.returncode == 0:
                    self.ap_manager.use_iwconfig = True
                    return True

            return False
        except subprocess.CalledProcessError:
            return False

    def interface_exists(self, iface=None):
        if not iface:
            iface = self.config.get("vwifi_iface", "xap0")

        net_dir = "/sys/class/net/"
        interfaces = os.listdir(net_dir)

        return iface in interfaces

    def get_all_mac_addresses(self) -> list:
        """Get all MAC addresses from all network interfaces"""
        macs = []
        net_dir = "/sys/class/net/"
        try:
            for iface in os.listdir(net_dir):
                addr_path = os.path.join(net_dir, iface, "address")
                if os.path.exists(addr_path):
                    with open(addr_path, "r") as f:
                        mac = f.read().strip()
                        if self.is_mac_address(mac):
                            macs.append(mac)
        except OSError:
            pass
        return macs

    def get_new_mac_address(self, iface=None):
        """Generate a new MAC address based on the current one"""
        iface = iface if iface else self.config["vwifi_iface"]

        old_mac = self.get_mac_address(iface)
        if not old_mac:
            return None

        # Extract the last byte and convert to integer
        last_byte_hex = old_mac.split(":")[-1]
        last_byte = int(last_byte_hex, 16)

        self.lock.mutex_lock()
        try:
            for i in range(1, 256):
                new_byte = (last_byte + i) % 256
                new_mac = f"{old_mac.rsplit(':', 1)[0]}:{new_byte:02x}"

                # Check if MAC address is already in use
                all_macs = self.get_all_mac_addresses()
                if new_mac not in all_macs:
                    return new_mac
        finally:
            self.lock.mutex_unlock()

        return None

    def is_interface_configured(self, iface=None) -> bool:
        return shared.is_interface_configured(iface)
