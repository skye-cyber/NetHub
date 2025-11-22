import argparse
import sys
import os
from ap_manager import ApManager
from ap_utils.config import config_manager, ConfigManager


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
    parser.add_argument('--ssid', help='SSID for the hotspot')
    parser.add_argument('--password', help='Password for the hotspot')
    parser.add_argument('--interface', help='Wireless interface to use')
    parser.add_argument('--mode', choices=['nmcli', 'systemd'], help='Hotspot mode')
    parser.add_argument('--psk', help='Use 64 hex digits pre-shared-key instead of passphrase')
    parser.add_argument('-m', "--method", default='bridge', help="Method for Internet sharing. Use: 'nat' for NAT (default) 'bridge' for bridging 'none' for no Internet sharing (equivalent to -n)")
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
    manager = ApManager()

    config_update(args)

    return
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
    if os.geteuid() != 0:
        print("This script must be run as root")
        sys.exit(1)
    main()
