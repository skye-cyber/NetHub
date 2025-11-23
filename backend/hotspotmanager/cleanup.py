import os
import sys
import signal
import subprocess
import shutil
from typing import List, Optional
from signals import SignalHandler


class CleanupManager(SignalHandler):
    def __init__(self, ap_man):
        # Ap man config
        self.ap_man = ap_man
        self.lock = self.ap_man.lock
        self.config = ap_man.config
        self.netmanager = self.ap_man.netmanager

        # Conf file config
        self.common_conf_dir = self.config['common_conf_dir'] or "/etc/ap_manager/conf"
        self.conf_dir = self.config['proc_dir'] or "/etc/ap_manager/proc"
        self.internet_iface = self.config.get('internet_iface', '')
        self.wifi_iface = self.config.get('wifi_iface', '')
        self.vwifi_iface = self.config.get('vwifi_iface', '')
        self.bridge_iface = self.config.get('bridge_iface', '')
        self.gateway = self.config.get('gateway', '')
        self.dns_port = self.config.get('dns_port', 53)
        self.share_method = self.config.get('share_method', 'none')
        self.no_dns = self.config.get('no_dns', False)
        self.no_virt = self.config.get('no_virt', False)
        self.running_as_daemon = self.config.get('daemon', False)
        self.daemon_pidfile = self.config.get('pidfile', '')  # Daemon pidfile
        self.old_macaddr = self.config.get('old_macaddr', '')

        # Unconfigured opts
        self.new_macaddr = self.config.get('new_macaddr', '')
        self.ip_addrs = self.config.get('ip_addrs', [])
        self.route_addrs = self.config.get('route_addrs', [])
        self.haveged_watchdog_pid = self.config.get('haveged_watchdog_pid', '')

    def _cleanup(self):
        """Internal cleanup function that performs all cleanup operations."""
        # Disable signal handling during cleanup
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGUSR1, signal.SIG_IGN)
        signal.signal(signal.SIGUSR2, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        self.lock.mutex_lock()

        try:
            # Disown all child processes
            subprocess.run(['disown', '-a'], shell=True)

            # Kill haveged_watchdog if running
            if self.haveged_watchdog_pid:
                try:
                    os.kill(int(self.haveged_watchdog_pid), signal.SIGTERM)
                except (OSError, ValueError):
                    pass

            # Kill processes from PID files
            if os.path.exists(self.conf_dir):
                for pid_file in os.listdir(self.conf_dir):
                    if pid_file.endswith('.pid'):
                        pid_path = os.path.join(self.conf_dir, pid_file)
                        try:
                            with open(pid_path, 'r') as f:
                                pid = int(f.read().strip())
                            os.kill(pid, signal.SIGKILL) if pid else None
                        except (IOError, ValueError, OSError):
                            pass

                # Remove the configuration directory
                shutil.rmtree(self.conf_dir, ignore_errors=True)

            # Check if we're the last instance using this internet interface
            found = False
            for conf_dir in self.list_running_conf():
                nat_internet_iface_path = os.path.join(conf_dir, 'nat_internet_iface')
                if os.path.exists(nat_internet_iface_path):
                    with open(nat_internet_iface_path, 'r') as f:
                        if f.read().strip() == self.internet_iface:
                            found = True
                            break

            if not found and self.internet_iface:
                # Restore original forwarding setting
                forwarding_file = os.path.join(self.common_conf_dir, f"{self.internet_iface}_forwarding")
                if os.path.exists(forwarding_file):
                    with open(forwarding_file, 'r') as src, open(f"/proc/sys/net/ipv4/conf/{self.internet_iface}/forwarding", 'w') as dst:
                        shutil.copyfileobj(src, dst)
                    os.remove(forwarding_file)

            # If we're the last instance, restore common settings
            if not self.has_running_instance():
                # Kill common processes
                if os.path.exists(self.common_conf_dir):
                    for pid_file in os.listdir(self.common_conf_dir):
                        if pid_file.endswith('.pid'):
                            pid_path = os.path.join(self.common_conf_dir, pid_file)
                            try:
                                with open(pid_path, 'r') as f:
                                    pid = int(f.read().strip())
                                os.kill(pid, signal.SIGKILL)
                            except (IOError, ValueError, OSError):
                                pass

                # Restore original ip_forward setting
                ip_forward_file = os.path.join(self.common_conf_dir, 'ip_forward')
                if os.path.exists(ip_forward_file):
                    with open(ip_forward_file, 'r') as src, open('/proc/sys/net/ipv4/ip_forward', 'w') as dst:
                        shutil.copyfileobj(src, dst)
                    os.remove(ip_forward_file)

                # Restore original bridge-nf-call-iptables setting
                bridge_nf_file = os.path.join(self.common_conf_dir, 'bridge-nf-call-iptables')
                if os.path.exists(bridge_nf_file):
                    if os.path.exists('/proc/sys/net/bridge/bridge-nf-call-iptables'):
                        with open(bridge_nf_file, 'r') as src, \
                                open('/proc/sys/net/bridge/bridge-nf-call-iptables', 'w') as dst:
                            shutil.copyfileobj(src, dst)
                    os.remove(bridge_nf_file)

                # Remove common configuration directory
                shutil.rmtree(self.common_conf_dir, ignore_errors=True)

            # Cleanup based on sharing method
            if self.share_method != 'none':
                if self.share_method == 'nat':
                    # Remove NAT rules
                    subprocess.run([
                        'iptables', '-w', '-t', 'nat', '-D', 'POSTROUTING',
                        '-s', f"{self.gateway.split('.')[0]}.{self.gateway.split('.')[1]}.{self.gateway.split('.')[2]}.0/24",
                        '!', '-o', self.wifi_iface, '-j', 'MASQUERADE'
                    ], check=False)
                    subprocess.run([
                        'iptables', '-w', '-D', 'FORWARD',
                        '-i', self.wifi_iface,
                        '-s', f"{self.gateway.split('.')[0]}.{self.gateway.split('.')[1]}.{self.gateway.split('.')[2]}.0/24",
                        '-j', 'ACCEPT'
                    ], check=False)
                    subprocess.run([
                        'iptables', '-w', '-D', 'FORWARD',
                        '-i', self.internet_iface,
                        '-d', f"{self.gateway.split('.')[0]}.{self.gateway.split('.')[1]}.{self.gateway.split('.')[2]}.0/24",
                        '-j', 'ACCEPT'
                    ], check=False)
                elif self.share_method == 'bridge':
                    # Remove bridge configuration if not already a bridge interface
                    if not self.ap_man.is_bridge_interface(self.internet_iface):
                        subprocess.run(['ip', 'link', 'set', 'dev', self.bridge_iface, 'down'], check=False)
                        subprocess.run(['ip', 'link', 'set', 'dev', self.internet_iface, 'down'], check=False)
                        subprocess.run(['ip', 'link', 'set', 'dev', self.internet_iface, 'promisc', 'off'], check=False)
                        subprocess.run(['ip', 'link', 'set', 'dev', self.internet_iface, 'nomaster'], check=False)
                        subprocess.run(['ip', 'link', 'delete', self.bridge_iface, 'type', 'bridge'], check=False)
                        subprocess.run(['ip', 'addr', 'flush', self.internet_iface], check=False)
                        subprocess.run(['ip', 'link', 'set', 'dev', self.internet_iface, 'up'], check=False)
                        self.dealloc_iface(self.bridge_iface)

                        # Restore original IP addresses
                        for addr in self.ip_addrs:
                            addr = addr.replace('inet', '').replace('secondary', '').replace('dynamic', '')
                            addr = addr.replace(f"{self.internet_iface}", '').strip()
                            subprocess.run(['ip', 'addr', 'add', addr, 'dev', self.internet_iface], check=False)

                        # Restore original routes
                        subprocess.run(['ip', 'route', 'flush', 'dev', self.internet_iface], check=False)
                        for route in self.route_addrs:
                            if route and not route.startswith('default'):
                                subprocess.run(['ip', 'route', 'add', route, 'dev', self.internet_iface], check=False)

                        # Add default routes last
                        for route in self.route_addrs:
                            if route and route.startswith('default'):
                                subprocess.run(['ip', 'route', 'add', route, 'dev', self.internet_iface], check=False)

                        # Remove from NetworkManager unmanaged list if needed
                        self.networkmanager_rm_unmanaged_if_needed(self.internet_iface)

            # Cleanup DNS if not disabled
            if self.share_method != 'bridge' and not self.no_dns:
                subprocess.run([
                    'iptables', '-w', '-D', 'INPUT',
                    '-p', 'tcp', '-m', 'tcp', '--dport', str(self.dns_port), '-j', 'ACCEPT'
                ], check=False)
                subprocess.run([
                    'iptables', '-w', '-D', 'INPUT',
                    '-p', 'udp', '-m', 'udp', '--dport', str(self.dns_port), '-j', 'ACCEPT'
                ], check=False)
                subprocess.run([
                    'iptables', '-w', '-t', 'nat', '-D', 'PREROUTING',
                    '-s', f"{self.gateway.split('.')[0]}.{self.gateway.split('.')[1]}.{self.gateway.split('.')[2]}.0/24",
                    '-d', self.gateway,
                    '-p', 'tcp', '-m', 'tcp', '--dport', '53',
                    '-j', 'REDIRECT', '--to-ports', str(self.dns_port)
                ], check=False)
                subprocess.run([
                    'iptables', '-w', '-t', 'nat', '-D', 'PREROUTING',
                    '-s', f"{self.gateway.split('.')[0]}.{self.gateway.split('.')[1]}.{self.gateway.split('.')[2]}.0/24",
                    '-d', self.gateway,
                    '-p', 'udp', '-m', 'udp', '--dport', '53',
                    '-j', 'REDIRECT', '--to-ports', str(self.dns_port)
                ], check=False)

            # Cleanup DHCP server
            if self.share_method != 'bridge':
                subprocess.run([
                    'iptables', '-w', '-D', 'INPUT',
                    '-p', 'udp', '-m', 'udp', '--dport', '67', '-j', 'ACCEPT'
                ], check=False)

            # Cleanup virtual interface if not disabled
            if not self.no_virt and self.vwifi_iface:
                subprocess.run(['ip', 'link', 'set', 'down', 'dev', self.vwifi_iface], check=False)
                subprocess.run(['ip', 'addr', 'flush', self.vwifi_iface], check=False)
                self.networkmanager_rm_unmanaged_if_needed(self.vwifi_iface, self.old_macaddr)
                subprocess.run(['iw', 'dev', self.vwifi_iface, 'del'], check=False)
                self.ap_man.dalloc_iface(self.vwifi_iface)
            else:
                # Cleanup main interface
                subprocess.run(['ip', 'link', 'set', 'down', 'dev', self.wifi_iface], check=False)
                subprocess.run(['ip', 'addr', 'flush', self.wifi_iface], check=False)
                if self.new_macaddr:
                    subprocess.run(['ip', 'link', 'set', 'dev', self.wifi_iface, 'address', self.old_macaddr], check=False)
                self.networkmanager_rm_unmanaged_if_needed(self.wifi_iface, self.old_macaddr)

        finally:
            self.lock.mutex_unlock()
            self.cleanup_lock()

            # Remove daemon PID file if running as daemon
            if self.running_as_daemon and self.daemon_pidfile and os.path.exists(self.daemon_pidfile):
                os.remove(self.daemon_pidfile)

    def cleanup(self):
        """Public cleanup function that provides user feedback."""
        print("\nDoing cleanup...", end=' ', flush=True)
        self._cleanup()
        print("done")

    def _die_(self, message: Optional[str] = None):
        """Handle fatal errors and exit."""
        if message:
            print(f"\nERROR: {message}\n", file=sys.stderr)
        # Send die signal to the main process if not the main process
        if os.getpid() != os.getppid():
            os.kill(os.getppid(), signal.SIGUSR2)
        sys.exit(1)

    def _clean_exit_(self):
        """Handle clean exits."""
        # Send clean_exit signal to the main process if not the main process
        if os.getpid() != os.getppid():
            os.kill(os.getppid(), signal.SIGUSR1)
        sys.exit(0)

    def has_running_instance(self) -> bool:
        """Check if there are any running instances."""
        return len(self.list_running_conf()) > 0

    def _is_bridge_interface_(self, iface: str) -> bool:
        """Check if an interface is a bridge interface."""
        return os.path.exists(f"/sys/class/net/{iface}/bridge")
