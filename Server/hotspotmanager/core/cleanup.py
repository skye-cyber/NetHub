import os
import sys
import signal
import subprocess
import shutil
from typing import Optional
from .signals import SignalHandler
from ap_utils.colors import fg
from .shared import shared


class CleanupManager(SignalHandler):
    def __init__(self, ap_man):
        # Initialize SignalHandler with config
        super().__init__(ap_man.config)

        # Ap man config
        self.ap_man = ap_man
        self.lock = self.ap_man.lock
        self.config = ap_man.config
        self.netmanager = self.ap_man.netmanager

        # Conf file config
        self.conf_dir = self.config['conf_dir'] or "/etc/ap_manager/conf"
        self.proc_dir = self.config['proc_dir'] or "/etc/ap_manager/proc"
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

    def nuke_processes(self):
        # Kill processes from PID files
        if os.path.exists(self.proc_dir):
            for pid_file in os.listdir(self.proc_dir):
                if pid_file.endswith('.pid'):
                    pid_path = os.path.join(self.proc_dir, pid_file)
                    try:
                        with open(pid_path, 'r') as f:
                            pid = int(f.read().strip())
                        os.kill(pid, signal.SIGKILL) if pid else None
                        # remove the pid file
                        os.remove(pid_path)
                    except (IOError, ValueError, OSError):
                        pass

            # Remove the processes directory if empty
            try:
                if os.path.exists(self.proc_dir) and not os.listdir(self.proc_dir):
                    os.rmdir(self.proc_dir)
            except OSError:
                pass

    def restore_config(self):
        # If we're the last instance, restore common settings
        if not self.has_running_instance():
            # Kill common processes
            if os.path.exists(self.proc_dir):
                for pid_file in os.listdir(self.proc_dir):
                    if pid_file.endswith('.pid'):
                        pid_path = os.path.join(self.conf_dir, pid_file)
                        try:
                            with open(pid_path, 'r') as f:
                                pid = int(f.read().strip())
                            os.kill(pid, signal.SIGKILL)
                            os.remove(pid_file)
                        except (IOError, ValueError, OSError):
                            pass

                # Restore original ip_forward setting
                ip_forward_file = os.path.join(self.conf_dir, 'ip_forward')
                if os.path.exists(ip_forward_file):
                    with open(ip_forward_file, 'r') as src, open('/proc/sys/net/ipv4/ip_forward', 'w') as dst:
                        shutil.copyfileobj(src, dst)
                    os.remove(ip_forward_file)

                # Restore original bridge-nf-call-iptables setting
                bridge_nf_file = os.path.join(self.conf_dir, 'bridge-nf-call-iptables')
                if os.path.exists(bridge_nf_file):
                    if os.path.exists('/proc/sys/net/bridge/bridge-nf-call-iptables'):
                        with open(bridge_nf_file, 'r') as src, \
                                open('/proc/sys/net/bridge/bridge-nf-call-iptables', 'w') as dst:
                            shutil.copyfileobj(src, dst)
                    os.remove(bridge_nf_file)

                # Remove common configuration directory if empty
                try:
                    if os.path.exists(self.conf_dir) and not os.listdir(self.conf_dir):
                        os.rmdir(self.conf_dir)
                except OSError:
                    pass

    def clean_nat(self):
        # Remove NAT rules
        try:
            subprocess.run([
                'iptables', '-w', '-t', 'nat', '-D', 'POSTROUTING',
                '-s', f"{self.gateway.rsplit('.', 1)[0]}.0/24",
                '!', '-o', self.wifi_iface, '-j', 'MASQUERADE'
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run([
                'iptables', '-w', '-D', 'FORWARD',
                '-i', self.wifi_iface,
                '-s', f"{self.gateway.rsplit('.', 1)[0]}.0/24",
                '-j', 'ACCEPT'
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run([
                'iptables', '-w', '-D', 'FORWARD',
                '-i', self.internet_iface,
                '-d', f"{self.gateway.rsplit('.', 1)[0]}.0/24",
                '-j', 'ACCEPT'
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            pass

    def clean_bridge(self):
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

    def clean_internet_sharing(self):
        # Cleanup based on sharing method
        if self.share_method == 'none':
            return

        if self.share_method == 'nat':
            return self.clean_nat()

        elif self.share_method == 'bridge':
            return self.clean_bridge()

    def clean_dns(self):
        # Cleanup DNS if not disabled
        if self.share_method == 'bridge' and self.no_dns:
            return

        try:
            subprocess.run([
                'iptables', '-w', '-D', 'INPUT',
                '-p', 'tcp', '-m', 'tcp', '--dport', str(self.dns_port), '-j', 'ACCEPT'
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            subprocess.run([
                'iptables', '-w', '-D', 'INPUT',
                '-p', 'udp', '-m', 'udp', '--dport', str(self.dns_port), '-j', 'ACCEPT'
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            subprocess.run([
                'iptables', '-w', '-t', 'nat', '-D', 'PREROUTING',
                '-s', f"{self.gateway.rsplit('.', 1)[0]}.0/24",
                '-d', self.gateway,
                '-p', 'tcp', '-m', 'tcp', '--dport', '53',
                '-j', 'REDIRECT', '--to-ports', str(self.dns_port)
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            subprocess.run([
                'iptables', '-w', '-t', 'nat', '-D', 'PREROUTING',
                '-s', f"{self.gateway.rsplit('.', 1)[0]}.0/24",
                '-d', self.gateway,
                '-p', 'udp', '-m', 'udp', '--dport', '53',
                '-j', 'REDIRECT', '--to-ports', str(self.dns_port)
            ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            pass

    def clean_dhcp(self):
        # Cleanup DHCP server
        if self.share_method != 'bridge':
            try:
                subprocess.run([
                    'iptables', '-w', '-D', 'INPUT',
                    '-p', 'udp', '-m', 'udp', '--dport', '67', '-j', 'ACCEPT'
                ], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception:
                pass

    def clean_hostapd(self) -> bool:
        pid_file = os.path.join(self.proc_dir, 'hostapd.pid')

        if self.config.get('daemon', False) and self.config['pidfile']:
            pid_file = self.config['pidfile']

        if not pid_file or not os.path.exists(pid_file):
            return False

        hostapd_pid = shared.get_hostapd_pid(pid_file)

        if hostapd_pid:
            try:
                os.kill(hostapd_pid)
                return True
            except Exception:
                return False
        return False

    def clean_interfaces(self):
        # Cleanup virtual interface if not disabled
        if not self.no_virt and self.vwifi_iface and self.ap_man.interface_manager.interface_exists(self.vwifi_iface):
            subprocess.run(['ip', 'link', 'set', 'down', 'dev', self.vwifi_iface], check=False)
            subprocess.run(['ip', 'addr', 'flush', self.vwifi_iface], check=False)

            self.networkmanager_rm_unmanaged_if_needed(self.vwifi_iface, self.old_macaddr)

            subprocess.run(['iw', 'dev', self.vwifi_iface, 'del'], check=False)

            self.ap_man.dalloc_iface(self.vwifi_iface)
        else:
            # Cleanup main interface
            subprocess.run(['ip', 'link', 'set', 'down', 'dev', self.wifi_iface], check=False)
            subprocess.run(['ip', 'addr', 'flush', self.wifi_iface], check=False)
            if self.new_macaddr and self.old_macaddr:
                subprocess.run(['ip', 'link', 'set', 'dev', self.wifi_iface, 'address', self.old_macaddr], check=False)
            self.networkmanager_rm_unmanaged_if_needed(self.wifi_iface, self.old_macaddr)

    def restore_forwarding_config(self):
        # Check if we're the last instance using this internet interface
        found = False
        for conf_dir in self.ap_man.network_config.list_running_conf():
            nat_internet_iface_path = os.path.join(conf_dir, 'nat_internet_iface')
            if os.path.exists(nat_internet_iface_path):
                with open(nat_internet_iface_path, 'r') as f:
                    if f.read().strip() == self.internet_iface:
                        found = True
                        break

        if not found and self.internet_iface:
            # Restore original forwarding setting
            forwarding_file = os.path.join(self.conf_dir, f"{self.internet_iface}_forwarding")
            if not os.path.exists(forwarding_file):
                return

            # if os.path.exists(forwarding_file):
            with open(forwarding_file, 'r') as src, open(f"/proc/sys/net/ipv4/conf/{self.internet_iface}/forwarding", 'w') as dst:
                shutil.copyfileobj(src, dst)
                os.remove(forwarding_file)

    def _cleanup(self):
        """Internal cleanup function that performs all cleanup operations."""
        # Disable signal handling during cleanup
        # signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGUSR1, signal.SIG_IGN)
        signal.signal(signal.SIGUSR2, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        self.lock.mutex_lock()

        try:
            # Disown all child processes
            subprocess.run(['which', 'disown'], shell=True)

            # Kill haveged_watchdog if running
            if self.haveged_watchdog_pid:
                try:
                    os.kill(int(self.haveged_watchdog_pid), signal.SIGTERM)
                except (OSError, ValueError):
                    pass

            # Clean process
            self.nuke_processes()

            self.restore_forwarding_config()

            # Restore settings/config
            self.restore_config()

            # clean internet sharing if any
            self.clean_internet_sharing()

            # Clean DNS
            self.clean_dns()

            self.clean_dhcp()

            self.clean_hostapd()

            # Stop ap_manager service -> delegated to interface_manager
            # shared.stop_service('ap_manager')
            # shared.kill_service('hostapd') ap_manager service shall terminate the proccess

            try:
                # Clean interfaces
                self.clean_interfaces()
            except Exception as e:
                print(f"{fg.RED}{e}{fg.RESET}")

            # Perfrom basic leanup
            self._basic_cleanup()
        except Exception as e:
            print(f"{fg.RED}{e}{fg.RESET}")
        finally:
            self.lock.mutex_unlock()
            self.lock.cleanup_lock()

            # Remove daemon PID file if running as daemon
            if self.running_as_daemon and self.daemon_pidfile and os.path.exists(self.daemon_pidfile):
                os.remove(self.daemon_pidfile)

    def cleanup(self):
        """Public cleanup function that provides user feedback."""
        print("\nDoing cleanup...", end='\n', flush=True)
        try:
            self._cleanup()
        except Exception as e:
            print(f"cleanup failed: {str(e)}")
            # Still try to do basic cleanup even if main cleanup fails
            self._basic_cleanup()

    def _die_(self, message: Optional[str] = None):
        """Handle fatal errors and exit."""
        if message:
            print(f"\nERROR: {message}\n", file=sys.stderr)
        # Send die signal to the main process if not the main process
        if os.getpid() != os.getppid():
            os.kill(os.getppid(), signal.SIGUSR2)
        sys.exit(1)

    def _basic_cleanup(self):
        """Basic cleanup that should always work."""
        print("Start Basic cleanup ...")
        try:
            # Kill any remaining processes
            if os.path.exists(self.proc_dir):
                for pid_file in os.listdir(self.proc_dir):
                    if pid_file.endswith('.pid'):
                        pid_path = os.path.join(self.proc_dir, pid_file)
                        try:
                            self.rm_proc(pid_path)
                        except (IOError, ValueError, OSError, ProcessLookupError):
                            pass

            try:
                if os.path.exists(self.COUNTER_LOCK_FILE):
                    os.remove(self.COUNTER_LOCK_FILE)
            except OSError:
                pass

            print("basic cleanup completed")
        except Exception:
            pass

    def rm_proc(self, pid_path):
        # Clean proccess with its files
        with open(pid_path, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
        finally:
            os.remove(pid_path)

        conf_dir = pid_path.strip('.pid')
        if os.path.exists(conf_dir):
            try:
                shutil.rmtree(conf_dir)
            except Exception:
                pass

    def _clean_exit_(self):
        """Handle clean exits."""
        # Send clean_exit signal to the main process if not the main process
        if os.getpid() != os.getppid():
            os.kill(os.getppid(), signal.SIGUSR1)
        sys.exit(0)

    def has_running_instance(self) -> bool:
        """Check if there are any running instances."""
        return len(self.ap_man.network_config.list_running_conf()) > 0

    def networkmanager_rm_unmanaged_if_needed(self, iface: str, mac: Optional[str] = None) -> bool:
        """Remove an interface from unmanaged list if needed."""
        if self.netmanager:
            return self.netmanager.networkmanager_rm_unmanaged_if_needed(iface, mac)
        return False

    def dealloc_iface(self, iface: str) -> None:
        """Deallocate an interface by removing its configuration file."""
        try:
            iface_conf = os.path.join(self.conf_dir, 'ifaces', iface)
            if os.path.exists(iface_conf):
                os.remove(iface_conf)
        except OSError:
            pass

    def _is_bridge_interface_(self, iface: str) -> bool:
        """Check if an interface is a bridge interface."""
        return os.path.exists(f"/sys/class/net/{iface}/bridge")

