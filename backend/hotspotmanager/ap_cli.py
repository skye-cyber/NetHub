import argparse
import sys
import re
import os
from ap_manager import ApManager
from ap_utils.config import config_manager, ConfigManager
import subprocess
import getpass

version = "1.0.0"


def config_update(args):
    try:
        args_dict = args.__dict__
        # Update Configuration
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
    parser = argparse.ArgumentParser(description='Custom Hotspot Manager')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'configure', 'interfaces'],
                        help='Action to perform')
    parser.add_argument('wifi_iface', default='wlan0', type=str, help='Wifi interface to use.')
    parser.add_argument('internet_iface', default="eth0", type=str, help='Internetfacing internet to use')
    parser.add_argument('--ssid', help='SSID for the hotspot')
    parser.add_argument('--password', help='Password for the hotspot')
    parser.add_argument('--interface', help='Wireless interface to use')
    parser.add_argument('--mode', choices=['nmcli', 'systemd'], help='Hotspot mode')
    parser.add_argument('--use_psk', action="store_true", help='Use 64 hex digits pre-shared-key instead of passphrase')
    parser.add_argument('--psk', help='64 hex digits pre-shared-key to be used.')
    parser.add_argument('-m', "--share-method", default='nat', choices=['nat', 'bridge', 'none'], help="Method for Internet sharing. 'none' for no Internet sharing (equivalent to -n)")
    parser.add_argument("-c", "--channel", default="6", help="Channel number (default: 6)")
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
    parser.add_argument("--freq-band", default="5GHz", help="Set frequency band. Valid inputs: 2.4, 5 (default: Use 5GHz if the interface supports it)")
    parser.add_argument("--driver", help="Choose your WiFi adapter driver (default: nl80211)")
    parser.add_argument("--no-virt", action='store_true', help="Do not create virtual interface")
    parser.add_argument("--no-haveged", action='store_true', help="Do not run 'haveged' automatically when needed")
    parser.add_argument("--fix-unmanaged", action='store_true', help="If NetworkManager shows your interface as unmanaged after you close create_ap, then use this option to switch your interface back to managed")
    parser.add_argument("--mac", help="Set MAC address")
    parser.add_argument("--dhcp-dns", help="Set DNS returned by DHCP <IP1[,IP2]>")
    parser.add_argument("--dhcp-hosts", help="<H1[,H2]> Add list of dnsmasq.conf 'dhcp-host='\
        values If ETC_HOSTS=1, it will use the ip addresses for the named hosts in that\
        /etc/hosts. Othwise, the following syntax would work --dhcp-hosts \'192.168.12.2, 192.168.12.3'  See https://github.com/imp/dnsmasq/blob/\
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
    parser.add_argument("--gateway", action='store_true', help="IPv4 Gateway for the Access Point (default: 192.168.100.1)")
    parser.add_argument("-d", action='store_true', help="DNS server will take into account /etc/hosts")
    parser.add_argument("-e", action='store_true', help="DNS server will take into account additional hosts file")

    parser.add_argument("--version", help="Print version number")

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        sys.exit(0)

    if args.version:
        sys.exit(version)

    if args.freq_band and args.freq_band != 5 and args.channel > 14:
        print("Channel number is greater than 14, assuming 5GHz frequency band")
        args.channel = 5

    # Update config
    manager = ApManager()

    if manager.is_wifi_interface(args.wifi_iface):
        sys.exit(f"ERROR: '{args.wifi_iface}' is not a WiFi interface")

    if manager.can_be_ap(args.wifi_iface):
        sys.exit("ERROR: Your adapter does not support AP (master) mode")

    if not manager.can_be_sta_and_ap(args.wifi_iface):
        if (manager.is_wifi_connected(args.wifi_iface)):
            sys.exit("ERROR: Your adapter can not be a station (i.e. be connected) and an AP at the same time")
        elif not args.no_virt:
            args.no_virt = False
            sys.exit("WARN: Your adapter does not fully support AP virtual interface, enabling --no-virt")
    if not manager.has_hostapd:
        sys.exit("ERROR: hostapd not found.")

    # ^(8192[cd][ue]|8723a[sue])$
    if manager.get_adapter_kernel_module(args.wifi_iface) == "^(8192[cd][ue]|8723a[sue])":
        if "rtl871xdrv" not in manager.where_hostapd:
            sys.exit("ERROR: You need to patch your hostapd with rtl871xdrv patches.")

    if args.driver != "rtl871xdrv":
        print("WARN: Your adapter needs rtl871xdrv, enabling --driver=rtl871xdrv")
        args.driver = "rtl871xdrv"

    if args.new:
        if not manager.is_macaddr(args.mac):
            sys.exit(f"ERROR: '{args.mac}' is not a valid MAC address")
        if manager.is_unicast_macaddr(args.mac):
            sys.exit(f"ERROR: The first byte of MAC address ({args.mac}) must be even")

        if args.mac in manager.get_all_macaddrs:
            print(f"WARN: MAC address '{args.mac}' already exists. Because of this, you may encounter some problems")

    if args.ssid and not (1 <= args.ssid <= 32):
        print(f"ERROR: Invalid SSID length {args.ssid} (expected 1..32)")

    if not args.use_psk and not args.password:
        password = None
        retries = 0
        while not password and retries < 3:
            password = getpass("Enter wifi password:")
            if not 8 <= args.password < 63:
                print("ERROR: Invalid passphrase length, (expected 8..63)... continuing without password")
                if retries < 3:
                    args.use_psk = False
                retries += 1
            else:
                args.password = password
                break

    if args.use_psk and not args.password:
        psk = None
        retries = 0
        while not psk and retries < 3:
            psk = getpass("Enter psk(pre-shared-key):")
            if args.password != 64:
                print("ERROR: Invalid psk length, (expected 64)... continuing without psk")
                retries += 1
            else:
                args.psk = psk
                break

    if args.share_method != "none" and manager.is_interface(args.internet_iface):
        sys.exit(f"ERROR: '{args.internet_iface}' is not an interface")

    if bool(re.search(r'{rtl\[0-9\]\.*}', manager.get_adapter_kernel_module(args.wifi_iface))):
        if args.password:
            print("WARN: Realtek drivers usually have problems with WPA1, enabling -w 2")
            args.wpa_version = 2
        print("WARN: If AP doesn't work, please read: howto/realtek.md")

    if args.no_virt and args.wifi_iface == args.internet_iface:
        sys.exit("ERROR: You can not share your connection from the same, interface if you are using --no-virt option.")

    config_update(args)
    manager._ap_init_()

    if args.list_running:
        manager.list_running()
    if args.list_clients:
        manager.print_client()

    if args.stop_pid:
        print(f"Trying to kill {args.stop_pid} instance associated with {args.stop_pid}...")
        manager.send_stop(args.stop_pid)
        sys.exit(0)

    if args.fix_unmanaged:
        print("Trying to fix unmanaged status in NetworkManager...")
        manager.netmanager.networkmanager_fix_unmanaged()
        sys.exit(0)

    # if args.daemon and
    # Assume we're running underneath a service manager if PIDFILE is set
    # and don't clobber it's output with a useless message
    print("Running as Daemon...")

    try:
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

    except KeyboardInterrupt:
        sys.exit('\nQuit')
    except Exception as e:
        sys.exit(e)


if __name__ == '__main__':
    # if os.geteuid() != 0:
    #   print("This script must be run as root")
    #   sys.exit(1)
    main()
