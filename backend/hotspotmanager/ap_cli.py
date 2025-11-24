#!/usr/bin/env python
import argparse
import sys
import re
import os
from ap_manager import ApManager
from ap_utils.config import config_manager, ConfigManager
import getpass
from typing import Union

version = "1.0.0"


def config_update(args):
    try:
        args_dict = args.__dict__
        # Update Configuration
        if args.config and os.path.exists(args.config):
            config_manager = ConfigManager(args.config)

        # Update main conf
        config_manager._dict_update(config_manager.get_config, args_dict)
        config_manager.save_config()

        # Update hostapd conf
        hostman = ConfigManager(config_manager.__bconfdir__ / 'hostapd.json')
        hostman._dict_update(None, args_dict)
        hostman.save_config()

        # Update network conf
        netman = ConfigManager(config_manager.__bconfdir__ / 'netconf.json')
        netman._dict_update(None, args_dict)
        netman.save_config()

        return True
    except KeyboardInterrupt:
        pass
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description='Custom AP Manager')
    parser.add_argument('--action', default='start', choices=['start', 'stop', 'status', 'configure', 'interfaces'], help='Action to perform')
    parser.add_argument('--wifi_iface', default='wlan0', type=str, help='Wifi interface to use.')
    parser.add_argument('--internet_iface', default="eth0", type=str, help='Internetfacing internet to use')
    parser.add_argument('--ssid', help='SSID for the hotspot')
    parser.add_argument('--password', help='Password for the hotspot')
    parser.add_argument('--interface', help='Wireless interface to use')
    parser.add_argument('--mode', choices=['nmcli', 'systemd'], help='Hotspot mode')
    parser.add_argument('--use_psk', action="store_true", help='Use 64 hex digits pre-shared-key instead of passphrase')
    parser.add_argument('--psk', help='64 hex digits pre-shared-key to be used.')
    parser.add_argument('-m', "--share-method", default='nat', choices=['nat', 'bridge', 'none'], help="Method for Internet sharing. 'none' for no Internet sharing (equivalent to -n)")
    parser.add_argument("-ch", "--channel", default=6, type=int, help="Channel number (default: 6)")
    parser.add_argument("-w", '--wpa-version', help="Use 1 for WPA, use 2 for WPA2, use 1+2 for both (default: 2)")
    parser.add_argument("-n", action='store_true', help="Disable Internet sharing (if you use this, don't pass the <interface-with-internet> argument)")

    parser.add_argument("--hidden", action='store_true', help="Make the Access Point hidden (do not broadcast the SSID)")
    parser.add_argument("--mac-filter", action='store_true', help="Enable MAC address filtering")
    parser.add_argument("--mac-filter-accept", action='store_true', help="Location of MAC address filter list (defaults to /etc/hostapd/hostapd.accept)")
    parser.add_argument("--redirect-to-localhost", action='store_true', help="If -n is set, redirect every web request to localhost (useful for public information networks)")
    parser.add_argument("--hostapd-debug", type=int, default=0, help="With level between 1 and 2, passes arguments -d or -dd to hostapd for debugging.")
    parser.add_argument("--hostapd-timestamps", action='store_true', help="Include timestamps in hostapd debug messages.")
    parser.add_argument("--isolate-clients", action='store_true', help="Disable communication between clients")
    parser.add_argument("--ieee80211n", action='store_true', help="Enable IEEE 802.11n (HT)")
    parser.add_argument("--ieee80211ac", action='store_true', help="Enable IEEE 802.11ac (VHT)")
    parser.add_argument("--ieee80211ax", action='store_true', help="Enable IEEE 802.11ax (VHT)")
    parser.add_argument("--ht_capab", help="HT capabilities (default: [HT40+])")
    parser.add_argument("--vht_capab", help="VHT capabilities")
    parser.add_argument("--country", help="Set two-letter country code for regularity (example: US)")
    parser.add_argument("--freq-band", default=5, type=Union[int, float], help="Set frequency band. Valid inputs: 2.4, 5 (default: Use 5GHz if the interface supports it)")
    parser.add_argument("--driver", help="Choose your WiFi adapter driver (default: nl80211)")
    parser.add_argument("--no-virt", action='store_true', help="Do not create virtual interface")
    parser.add_argument("--no-haveged", action='store_true', help="Do not run 'haveged' automatically when needed")
    parser.add_argument("--fix-unmanaged", action='store_true', help="If NetworkManager shows your interface as unmanaged after you close create_ap, then use this option to switch your interface back to managed")
    parser.add_argument("--mac", type=str, help="Set MAC address")
    parser.add_argument("--dhcp-dns", nargs="+", help="Set DNS returned by DHCP <IP1[,IP2]>")
    parser.add_argument("--dhcp-hosts", nargs="+", help="<H1 H2> Add list of dnsmasq.conf 'dhcp-host='\
        values If ETC_HOSTS=1, it will use the ip addresses for the named hosts in that\
        /etc/hosts. Othwise, the following syntax would work --dhcp-hosts \'192.168.12.2' '192.168.12.3'  See https://github.com/imp/dnsmasq/blob/\
        770bce967cfc9967273d0acfb3ea018fb7b17522/dnsmasq.conf.example#L238 for other valid\
        dnsmasq dhcp-host parameters.")
    parser.add_argument("--daemon", action='store_true', help="Run create_ap in the background")
    parser.add_argument("--pidfile", help="Save daemon PID to file")
    parser.add_argument("--logfile", help="Save daemon messages to file")
    parser.add_argument("--dns-logfile", help="Log DNS queries to file")
    parser.add_argument("--stop-pid", type=int, help="Send stop command to an already running create_ap. For an <id> you can put the PID of create_ap or the WiFi interface. You can get them with --list-running")
    parser.add_argument("--list-running", action='store_true', help="Show the create_ap processes that are already running")
    parser.add_argument("--list-clients", action='store_true', help="List the clients connected to create_ap instance associated with <id>.  For an <id> you can put the PID of create_ap or the WiFi interface. If virtual WiFi interface was created, then use that one. You can get them with --list-running")

    # parser.add_argument("Non-Bridging Options:")
    parser.add_argument("--no-dns", action='store_true', help="Disable dnsmasq DNS server")
    parser.add_argument("--no-dnsmasq", action='store_true', help="Disable dnsmasq server completely")
    parser.add_argument("--gateway", type=str, help="IPv4 Gateway for the Access Point (default: 192.168.100.1)")
    parser.add_argument("-d", action='store_true', help="DNS server will take into account /etc/hosts")
    parser.add_argument("-e", action='store_true', help="DNS server will take into account additional hosts file")
    parser.add_argument("-c", "--config", help="Config file with default values.")

    parser.add_argument("--version", action="store_true", help="Print version number")

    args = parser.parse_args()

    validate_arguments(args)


class ArgumentValidator:
    def __init__(self, manager):
        self.manager = manager
        self.args = None
        self.validation_map = {
            'version': self._validate_version,
            'freq_band': self._validate_freq_band,
            'wifi_interface': self._validate_wifi_interface,
            'ap_support': self._validate_ap_support,
            'sta_ap_conflict': self._validate_sta_ap_conflict,
            'hostapd': self._validate_hostapd,
            'rtl871x': self.validate_rtl871x,
            'mac_address': self._validate_mac_address,
            'ssid': self._validate_ssid,
            'password': self._validate_password,
            'psk': self._validate_psk,
            'internet_interface': self._validate_internet_interface,
            'realtek_warning': self._validate_realtek_warning,
            'virtual_interface': self._validate_virtual_interface
        }

    def validate(self, args):
        """Validate all arguments using the validation map."""
        self.args = args
        for key, validator in self.validation_map.items():
            validator(args)

        return args

    def _validate_version(self, args):
        """Handle version request."""
        if args.version:
            sys.exit(version)

    def _validate_freq_band(self, args):
        """Validate frequency band and channel settings."""
        if args.freq_band and int(args.freq_band) != 5 and int(args.channel) > 14:
            print("Channel number is greater than 14, assuming 5GHz frequency band")
            args.channel = 5

    def _validate_wifi_interface(self, args):
        """Validate WiFi interface."""
        if not self.manager.is_wifi_interface(args.wifi_iface):
            sys.exit(f"ERROR: '{args.wifi_iface}' is not a WiFi interface")

    def _validate_ap_support(self, args):
        """Validate AP mode support."""
        if not self.manager.can_be_ap(args.wifi_iface):
            sys.exit("ERROR: Your adapter does not support AP (master) mode")

    def _validate_sta_ap_conflict(self, args):
        """Validate STA and AP mode conflict."""
        if not self.manager.can_be_sta_and_ap(args.wifi_iface):
            if self.manager.is_wifi_connected(args.wifi_iface):
                sys.exit("ERROR: Your adapter can not be a station and an AP at the same time")
            elif not args.no_virt:
                args.no_virt = False
                print("WARN: Your adapter does not fully support AP virtual interface, enabling --no-virt")

    def _validate_hostapd(self, args):
        """Validate hostapd availability."""
        if not self.manager.has_hostapd:
            sys.exit("ERROR: hostapd not found.")

    def validate_rtl871x(self, args):
        """Validate RTL871x driver requirements."""
        # Check if the kernel module matches the pattern
        kernel_module = self.manager.get_adapter_kernel_module(args.wifi_iface)
        if re.match(r'^(8192[cd][ue]|8723a[sue])$', kernel_module):
            # Check if hostapd has the rtl871xdrv patch
            try:
                with open(self.manager.where_hostapd, 'rb') as f:
                    if b'rtl871xdrv' not in f.read():
                        sys.exit("ERROR: You need to patch your hostapd with rtl871xdrv patches.")
            except IOError:
                sys.exit("ERROR: Could not read hostapd binary.")

    def _validate_mac_address(self, args):
        """Validate MAC address."""
        if args.mac:
            if not self.manager.is_macaddr(args.mac):
                sys.exit(f"ERROR: '{args.mac}' is not a valid MAC address")

            if self.manager.is_unicast_macaddr(args.mac):
                sys.exit(f"ERROR: The first byte of MAC address ({args.mac}) must be even")

            if args.mac in self.manager.get_all_macaddrs():
                print(f"WARN: MAC address '{args.mac}' already exists. Because of this, you may encounter some problems")

    def _validate_ssid(self, args):
        """Validate SSID length."""
        if args.ssid and not (1 <= len(args.ssid) <= 32):
            sys.exit(f"ERROR: Invalid SSID length {len(args.ssid)} (expected 1..32)")

    def _validate_password(self, args):
        """Validate password input."""
        if not args.use_psk and not args.password:
            default_paswd = self.manager.config.get('password', None)
            if default_paswd:
                args.password = default_paswd
                return default_paswd

            args.password = self._get_password_input(
                "Enter wifi password:",
                min_length=8,
                max_length=63
            )

    def _validate_psk(self, args):
        """Validate PSK input."""
        if args.use_psk and not args.psk:
            default_psk = self.manager.config.get('psk', None)
            if default_psk:
                args.password = default_psk
                return default_psk

            args.psk = self._get_password_input(
                "Enter psk(pre-shared-key):",
                length=64
            )

    def _validate_internet_interface(self, args):
        """Validate internet interface for sharing."""
        if args.share_method != "none" and not self.manager.is_interface(args.internet_iface):
            sys.exit(f"ERROR: '{args.internet_iface}' is not an interface")

    def _validate_realtek_warning(self, args):
        """Handle Realtek driver warnings."""
        if bool(re.search(r'{rtl\[0-9\]\.*}', self.manager.get_adapter_kernel_module(args.wifi_iface))):
            if args.password:
                print("WARN: Realtek drivers usually have problems with WPA1, enabling -w 2")
                args.wpa_version = 2
            print("WARN: If AP doesn't work, please read: howto/realtek.md")

    def _validate_virtual_interface(self, args):
        """Validate virtual interface settings."""
        if args.no_virt and args.wifi_iface == args.internet_iface:
            sys.exit("ERROR: You can not share your connection from the same interface if you are using --no-virt option.")

            config_update(args)
            self.manager._ap_init_()

    def _get_password_input(self, prompt, min_length=None, max_length=None, length=None):
        """Get password input with validation."""
        retries = 0
        while retries < 3:
            password = getpass.getpass(prompt)
            if length and len(password) != length:
                print(f"ERROR: Invalid length, expected {length} characters")
            elif min_length and len(password) < min_length:
                print(f"ERROR: Too short, minimum {min_length} characters required")
            elif max_length and len(password) > max_length:
                print(f"ERROR: Too long, maximum {max_length} characters allowed")
            else:
                return password
            retries += 1
        return None


def validate_arguments(args):
    """Main validation function that uses the ArgumentValidator class."""
    try:
        manager = ApManager()
        validator = ArgumentValidator(manager)

        validator.validate(args)

        config_update(args)

        if args.action == 'start':
            return manager._ap_init_()
        elif args.action == 'stop':
            return manager.stop_hotspot()
        elif args.action == 'status':
            return manager.show_status()
        elif args.action == 'configure':
            return manager.configure(args.ssid, args.password, args.interface, args.mode)
        elif args.action == 'interfaces':
            interfaces = manager.get_available_interfaces()
            print("Available wireless interfaces:")
            for iface in interfaces:
                print(f"  - {iface}")
        return manager
    except KeyboardInterrupt:
        sys.exit('\nQuit')
    except Exception as e:
        sys.exit(e)


if __name__ == '__main__':
    # if os.geteuid() != 0:
    #   print("This script must be run as root")
    #   sys.exit(1)
    main()
