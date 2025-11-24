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
        self.lock.mutex_lock()
        conf_dir = self.config['proc_dir']

        os.makedirs(self.config['common_conf_dir'], exis_ok=True)

        with open(os.path.join(conf_dir, 'pid', 'w')) as tmpf:
            tmpf.write(os.getpid())

        # to make --list-running work from any user, we must give read
        # permissions to conf_dir and conf_dir/pid
        os.chown(conf_dir, '755')
        os.chown(tmpf, '444')

        with open(os.path.join(conf_dir, 'nat_internet_iface')) as f:
            f.write(self.config['internet_iface'])

        shutil.copytree(f"/proc/sys/net/ipv4/conf/{self.config['internet_iface']}/forwarding", os.path.join(conf_dir, f"{self.config['internet_iface']}_forwarding"), dirs_exist_ok=True)

        shutil.copytree(f"/proc/sys/net/ipv4/ip_forward", conf_dir, dirs_exist_ok=True)

        if os.path.exists('/proc/sys/net/bridge/bridge-nf-call-iptables'):
            shutil.copytree('/proc/sys/net/bridge/bridge-nf-call-iptables', conf_dir, dirs_exist_ok=True)

        self.lock.mutex_unlock()

        if self.config['share_method'] == "bridge":
            if self.is_bridge_interface(self.config['internet_iface']):
                self.config.update({'bridge_iface': self.config['internet_iface']})
            else:
                self.config.update({'bridge_iface': self.alloc_new_iface('xbr')})

        if self.use_iwconfig:
            subprocess.run(['iw', 'dev', self.config['wifi_iface'], 'set', 'power_save', 'off'])

        self.iface_freq_channel_setup()

        if self.config['no_virt']:
            self.config.update({'vwifi_iface': self.alloc_new_iface('xap')})

            # in NetworkManager 0.9.9 and above we can set the interface as unmanaged without
            # the need of MAC address, so we set it before we create the virtual interface.
            if self.netmanager.networkmanager_is_running() and self.netmanager.NM_OLDER_VERSION == 0:
                print(f"Network Manager found, set {self.config['vwifi_iface']} as unmanaged device... ")
                self.netmanager.networkmanager_add_unmanaged(self.config['vwifi_iface'])
                # do not call networkmanager_wait_until_unmanaged because interface does not
                # exist yet
                print("DONE")

            # Update and Save config
            self.config = self.config_manager._dict_update(None, self.config)
            self.config_manager.save_config()

            # Create virtual interface
            self.create_virt_iface()
        # else:

        self.lock.mutex_lock()
        wif_iface_conf = os.path.join(conf_dir, 'wifi_ifaces')
        with open(wif_iface_conf, 'w') as f:
            f.write(self.config['wifi_iface'])
        os.chown(wif_iface_conf, 444)
        self.lock.mutex_unlock()

        if self.config['country'] and self.use_iwconfig:
            subprocess.run(['iw', 'reg', 'set', self.config['country']])

        self.make_unmanaged()

        if self.config['hidden']:
            print("Access Point's SSID is hidden!")
        if self.config['mac_filter']:
            print("MAC address filtering is enabled!")
        if self.config['isolate_clients']:
            print("Access Point's clients will be isolated!")

        self.config_hostapd()
        self.config_dnsmaq()
        self.init_wifi_iface()
        self.enable_internet_sharing()
        self.start_dhcp_dns()
        self.start_ap()
        self.start_hostapd()
        self.clean.clean_exit("Success")

    def start_ap(self):
        print(f"hostapd command-line interface: hostapd_cli -p {self.conf_dir}/hostapd_ctrl")
        if self.config['no_haveged']:
            self.haveged_watchdog()
            # HAVEGED_WATCHDOG_PID =

    def enable_internet_sharing(self):
        # enable Internet sharing
        if self.config['share_method'] != 'none':
            print(f"Sharing Internet using method: {self.config['share_method']}")
            if self.config['share_method'] == "nat":
                if subprocess.run(['iptables', '-w', '-t', 'nat', '-I', 'POSTROUTING', '-s', f"{self.config['gateway']:.*}.0/24", '!', '-o', self.config['wifi_iface'], '-j', 'MASQUERADE'], check=True, capture_output=True, text=True).returncode != 0:
                    sys.exit(1)

                if subprocess.run(['iptables', '-w', '-I', 'FORWARD', '-i', self.config['wifi_iface'], '-s', f"{self.config['gateway']:.*}.0/24", '-j', 'ACCEPT'], check=True, capture_output=True, text=True).returncode != 0:
                    sys.exit(1)

                if subprocess.run(['iptables', '-w', '-I', 'FORWARD', '-i', self.config['internet_iface'], '-d', f"{self.config['gateway']:.*}.0/24", '-j', 'ACCEPT'], check=True, capture_output=True, text=True).returncode != 0:
                    sys.exit(1)

                try:
                    with open(f"/proc/sys/net/ipv4/conf/{self.config['internet_iface']}/forwarding", 'w') as f:
                        f.write(1)
                    with open("/proc/sys/net/ipv4/ip_forward", 'w') as f:
                        f.write(1)
                except IOError:
                    sys.exit("Could not write file")
                except Exception:
                    sys.exit(1)

                # to enable clients to establish PPTP connections we must
                # load nf_nat_pptp module
                subprocess.run(['modprobe', 'nf_nat_pptp'])
            if self.config['share_method'] == "bridge":
                # disable iptables rules for bridged interfaces
                if os.path.exists("/proc/sys/net/bridge/bridge-nf-call-iptables"):
                    with open("/proc/sys/net/bridge/bridge-nf-call-iptables", 'w') as f:
                        f.write(0)

                """ to initialize the bridge interface correctly we need to do the following:

                 1) save the IPs and route table of INTERNET_IFACE
                 2) if NetworkManager is running set INTERNET_IFACE as unmanaged
                 3) create BRIDGE_IFACE and attach INTERNET_IFACE to it
                 4) set the previously saved IPs and route table to BRIDGE_IFACE

                 we need the above because BRIDGE_IFACE is the master interface from now on
                 and it must know where is connected, otherwise connection is lost.
                """
                if self.is_bridge_interface(self.config['internet_iface']):
                    print("Create a bridge interface... ")
                    old_ifaces = None
                    IP_ADDRS = re.search(r'inet\s([1-9]+(.?[1-9]+)+)', subprocess.run(['ip', 'addr', 'show', self.config['internet_iface']], check=True, capture_output=True, text=True).stdout)
                    ROUTE_ADDRS = subprocess.run(['ip', 'route', 'show', 'dev', self.config['internet_iface']], check=True, capture_output=True, text=True).stdout
                    if self.netmanager.networkmanager_is_running():
                        self.netmanager.networkmanager_add_unmanaged(self.config['internet_iface'])
                        self.netmanager.networkmanager_wait_until_unmanaged(self.config['internet_iface'])
                    # create bridge interface
                    if subprocess.run(['ip', 'link', 'add', 'name', self.config['bridge_iface'], 'type', 'bridge'], check=True, capture_output=True, text=True).returncode != 0:
                        sys.exit(1)
                    if subprocess.run(['ip', 'link', 'set', 'dev', self.config['bridge_iface'], 'up'], check=True, capture_output=True, text=True).returncode != 0:
                        sys.exit(1)
                    # set 0ms forward delay
                    with open(f"/sys/class/net/{self.config['bridge_iface']}/bridge/forward_delay", 'w') as f:
                        f.write(0)

                    # attach internet interface to bridge interface
                    if subprocess.run(['ip', 'link', 'set', 'dev', self.config['internet_iface'], 'promisc', 'on'], check=True, capture_output=True, text=True).returncode != 0:
                        sys.exit(1)
                    if subprocess.run(['ip', 'link', 'set', 'dev', self.config['internet_iface'], 'up'], check=True, capture_output=True, text=True).returncode != 0:
                        sys.exit(1)
                    if subprocess.run(['ip', 'link', 'set', 'dev', self.config['internet_iface'], 'master', self.config['bridge_iface']], check=True, capture_output=True, text=True).returncode != 0:
                        sys.exit(1)

                    subprocess.run(['ip', 'addr', 'flush', self.config['internet_iface']], check=True, capture_output=True, text=True)

                    for x in IP_ADDRS:
                        x = f"{x}/inet/"
                        x = f"{x}/secondary/"
                        x = f"{x}/dynamic/"
                        x = re.search(r's/\([0-9]\)sec/\1/g', x)
                        x = f"{x}/{self.config['internet_iface']}/"

                        if subprocess.run(['ip', 'addr', 'add', x, 'dev', self.config['bridge_iface']]).returncode != 0:
                            sys.exit(1)

                    # remove any existing entries that were added from 'ip addr add'
                    subprocess.run(['ip', 'route', 'flush', 'dev', self.config['internet_iface']], check=True, capture_output=True, text=True)
                    subprocess.run(['ip', 'route', 'flush', 'dev', self.config['bridge_iface']], check=True, capture_output=True, text=True)

                    # we must first add the entries that specify the subnets and then the
                    # gateway entry, otherwise 'ip addr add' will return an error
                    for x in ROUTE_ADDRS:
                        if 'default' in x:
                            continue
                        if subprocess.run(['ip', 'route', 'add', x, 'dev', self.config['bridge_iface']]).returncode != 0:
                            sys.exit(0)
                    for x in ROUTE_ADDRS:
                        if 'default' not in x:
                            continue
                        if subprocess.run(['ip', 'route', 'add', x, 'dev', self.config['bridge_iface']]).returncode != 0:
                            sys.exit(0)
                    print(f"{self.config['bridge_iface']} created")
        else:
            print("No Internet sharing")

    def start_hostapd(self):
        # start hostapd (use stdbuf when available for no delayed output in programs that redirect stdout)
        res = subprocess.run(['which', 'stdbuf'], check=True, capture_output=True, text=True)
        STDBUF_PATH = res.stdout if res.returncode == 0 else None

        hostapd = subprocess.run(['stdbuf', '-oL'], check=True, capture_output=True, text=True)

        # get hostapd pid
        HOSTAPD_PID = os.getppid(hostapd)
        with open(os.apth.join(self.conf_dir, 'hostapd.pid')) as f:
            f.write(HOSTAPD_PID)

        print("Error: Failed to run hostapd, maybe a program is interfering.")

        if self.netmanager.networkmanager_is_running():
            print("If an error like 'n80211: Could not configure driver mode' was thrown, try running the following before starting ap_manager:")

            if self.nm_older_version:
                print("    nmcli nm wifi off")
            else:
                print("    nmcli r wifi off")
            print("    rfkill unblock wlan")

    def start_dhcp_dns(self):
        # start dhcp + dns (optional)
        if self.config['share_method'] != 'bridge':
            if not self.config['no_dns']:
                if subprocess.run(['iptables', '-w', '-I', 'INPUT', '-p', 'tcp', '-m', 'tcp', '--dport ', self.config.get('dns_port', 53), '-j', 'ACCEPT'], check=True, capture_output=True, text=True).returncode != 0:
                    sys.exit(1)
                if subprocess.run(['iptables', '-w', '-I', 'INPUT', '-p', 'udp', '-m', 'udp', '--dport', self.config.get('dns_port', 53), '-j', 'ACCEPT'], check=True, capture_output=True, text=True).returncode != 0:
                    sys.exit(1)
                if subprocess.run(['iptables', '-w', '-t', 'nat', '-I', 'PREROUTING', '-s', f"{self.config['gateway']:.*}.0/24", '-d', self.config['gateway'], '-p', 'tcp', '-m', 'tcp', '--dport', 53, '-j', 'REDIRECT', '--to-ports', self.config.get('dns_port', 53)], check=True, capture_output=True, text=True).returncode != 0:
                    sys.exit(1)
                if subprocess.run(['iptables', '-w', '-t', 'nat', '-I', 'PREROUTING', '-s' f"{self.config['gateway']:.*}.0/24", '-d', self.config['gateway'], '-p', 'udp', '-m', 'udp', '--dport', '53', '-j', 'REDIRECT', '--to-ports', self.config.get('dns_port', 53)], check=True, capture_output=True, text=True).returncode != 0:
                    sys.exit(1)

            if not self.config['no_dnsmasq']:
                if subprocess.run(['iptables', '-w', '-I', 'INPUT', '-p', 'udp', '-m', 'udp', '--dport', 67, '-j', 'ACCEPT'], check=True, capture_output=True, text=True).returncode != 0:
                    sys.exit(1)

                # apparmor does not allow dnsmasq to read files.
                # remove restriction.
                COMPLAIN_CMD = ['command', '-v', 'complain'] if subprocess.run(['command', '-v', 'complain'], check=True, capture_output=True, text=True).stdout else ['command', '-v', 'aa-complain'] if subprocess.run(['command', '-v', 'complain'], check=True, capture_output=True, text=True).stdout else None

                if COMPLAIN_CMD:
                    subprocess.run(COMPLAIN_CMD.append('dnsmasq'), check=True, capture_output=True, text=True)

                os.umask(0o033)
                if subprocess.run(['dnsmasq', '-C', os.path.join(self.conf_dir, 'dnsmasq.conf'), '-x', os.path.join(self.conf_dir, 'dnsmasq.pid'), '-l', os.path.join(self.conf_dir, 'dnsmasq.lease'), '-p', self.config['dns_port']], check=True, capture_output=True, text=True).returncode != 0:
                    sys.exit(1)

                os.umask(self.SCRIPT_UMASK)

    def init_wifi_iface(self):
        # initialize WiFi interface
        if not self.config['no_virt'] and self.config['mac']:
            if subprocess.run(['ip', 'link', 'set', 'dev', self.config['wifi_iface'], 'address', self.config['mac']], check=True, capture_output=True, text=True).returncode != 0:
                sys.exit(self.virt_diems)

        if subprocess.run(['ip', 'link', 'set', 'down', 'dev', self.config['wifi_iface']], check=True, capture_output=True, text=True).returncode != 0:
            sys.exit(self.virt_diems)

        if subprocess.run(['ip', 'addr', 'flush', self.config['wifi_iface']], check=True, capture_output=True, text=True).returncode != 0:
            sys.exit(self.virt_diems)

        if self.config['no_virt'] and self.config['mac']:
            if subprocess.run(['ip', 'link', 'set', 'dev', self.config['wifi_iface'], 'address', self.config['mac']], check=True, capture_output=True, text=True).returncode != 0:
                sys.exit(self.virt_diems)

        if self.config['share_method'] != 'bridge':
            if subprocess.run(['ip', 'link', 'set', 'up', 'dev', self.config['wifi_iface']], check=True, capture_output=True, text=True).returncode != 0:
                sys.exit(self.virt_diems)
            if subprocess.run(['ip', 'addr', 'add', f"{self.config['gateway']}/24", 'broadcast', f"{self.config['gateway']:.*}.255", 'dev', self.config['wifi_iface']], check=True, capture_output=True, text=True).returncode != 0:
                sys.exit(self.virt_diems)
        return True

    def config_dnsmaq(self):
        if not self.config['no_dnsmasq']:
            # setup dnsmasq config (dhcp + dns)
            dnsmasq_info = subprocess.run(['dnsmasq', '-v'], check=True, capture_output=True, text=True)
            if not dnsmasq_info.returncode == 0:
                sys.exit("DNSMASQ not installed")

            dnsmasq_version = re.search(r'[0-9]+(\.[0-9]+)*\.[0-9]+', dnsmasq_info.stdout).group(0)
            cmp_res = self.netmanager.version_cmp(dnsmasq_version, '2.63')

            if res == 1:
                dnsmasq_bind = 'bind-interfaces'
            else:
                dnsmasq_bind = 'bind-dynamic'
            if self.config['dhcp_dns'] == 'gateway':
                dhcp_dns = 'gateway'

            mtu = self.get_mtu(self.config['internet_iface'])

            with open(os.path.join(self.conf_dir, 'dnsmasq.conf'), 'w') as f:
                f.write(
                    (
                        f"listen-address={self.config['gateway']}\n"
                        f"{dnsmasq_bind}\n"
                        f"dhcp-range={self.config['gateway']:.*}.1,{self.config['gateway']:.*}.254,255.255.255.0,24h\n"
                        f"dhcp-option-force=option:router,{self.config['gateway']}\n"
                        f"dhcp-option-force=option:dns-server,{','.join(self.config['dhcp_dns']).strip()}\n" if (self.config['dhcp_dns'] == 'gateway' and len(self.config['dhcp_dns']) > 0) else ''
                    ).strip()
                )

                if not self.config['etc_hosts'] or len(self.config['etc_hosts']) > 0:
                    f.write((
                        'no-hosts\n'
                    ))
                if len(self.config['addn_hosts']) > 0:
                    f.write((
                        f"addn-hosts={','.join(self.config['addn_hosts']).strip()}\n"
                    ))
                if mtu:
                    f.write((
                        f"dhcp-option-force=option:mtu,{mtu}\n"
                    ))
                if self.config['dhcp_hosts'] and len(self.config['dhcp_hosts']) > 0:
                    f.write((
                        '\n'.join(f"dhcp-host={host}" for host in self.config['dhcp_hosts']).strip()
                    ))
                if self.config['dns_logfile']:
                    f.write((
                        "log-queries\n"
                        f"log-facility={self.config['dns_logfile']}\n"
                    ))
                if self.config['share_method'] == 'none' and self.config['redirect_to_localhost']:
                    f.write((
                        f"address=/#/{self.config['gateway']}"
                    ))
        return True

    def config_hostapd(self):
        # hostapd config
        config = (
            "beacon_int=100\n"
            f"ssid={self.config['ssid']}\n"
            "interface={WIFI_IFACE}"
            f"driver={self.config['driver']}\n"
            f"channel={self.config['channel']}\n"
            f"ctrl_interface={os.path.join(self.conf_dir, 'hostapd_ctrl')}\n"
            "ctrl_interface_group=0\n"
            f"ignore_broadcast_ssid={self.config['hidden']}\n"
            f"ap_isolate={self.config['isolate_clients']}\n"
        )
        with open(os.path.join(self.conf_dir, 'hostapd.conf'), 'w') as f:
            f.write(config)
            if self.config['country']:
                f.write((
                    f"country_code={self.config['country']}\n"
                    "ieee80211d=1\n"
                ))
            if float(self.config['freq_band']) == 2.4:
                f.write((
                    "hw_mode=g\n"
                ))
            else:
                f.write((
                    "hw_mode=a\n"
                ))

            if self.config['mac_filter']:
                f.write((
                    f"macaddr_acl={self.config['mac_filter']}\n"
                    f"accept_mac_file={self.config['mac_filter_accept']}\n"
                ))
            if self.config['ieee80211n']:
                f.write((
                    "ieee80211n=1\n"
                    f"ht_capab={self.config['ht_capab']}\n"
                ))
            if self.config['ieee80211ac']:
                f.write((
                    "ieee80211ac=1\n"
                ))
            if self.config['ieee80211ax']:
                f.write((
                    "ieee80211ax=1"
                ))
            if self.config['vht_capab']:
                f.write((
                    f"vht_capab={self.config['vht_capab']}\n"
                ))
            if self.config['wmm_enabled']:
                f.write((
                    "wmm_enabled=1\n"
                ))
            if not self.config['password']:
                if self.config['wpa_version'] == "1+2":
                    self.config.update({'wpa_version': 2})  # Assuming you want to default to WPA2 for the "1+2" setting
                if not self.config['use_psk']:
                    wpa_key_type = "passphrase"
                else:
                    wpa_key_type = "psk"
                if self.config['wpa_version'] == 3:
                    # Configuring for WPA3 Transition Mode
                    # 80211w must be 1 or Apple Devices will not connect.
                    # 1 is the only valid value for WPA3 Transition Mode
                    f.write((
                        "wpa=2\n"
                        f"wpa_{wpa_key_type}={self.config['password']}\n"
                        "wpa_key_mgmt=WPA-PSK SAE\n"
                        "wpa_pairwise=CCMP\n"
                        "rsn_pairwise=CCMP\n"
                        "ieee80211w=1\n"
                    ))
                else:
                    f.write((
                        f"wpa={self.config['wpa_version']}\n"
                        f"wpa_{wpa_key_type}={self.config['password']}\n"
                        "wpa_key_mgmt=WPA-PSK\n"
                        "wpa_pairwise=CCMP\n"
                        "rsn_pairwise=CCMP\n"
                    ))
                if self.config['share_method'] == "bridge":
                    f.write((
                        f"bridge={self.config['bridge_iface']}"
                    ))
        return True

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
