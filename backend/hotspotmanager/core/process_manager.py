#!/usr/bin/env python3
"""
Process Manager Module
Handles process tracking, instance management, and inter-process communication
"""
import os
import signal
import subprocess
import sys
from typing import Optional, List
from .lock import lock
import time


class ProcessManager:
    def __init__(self, ap_manager):
        """Initialize ProcessManager with reference to main AP manager"""
        self.ap_manager = ap_manager
        self.config = ap_manager.config
        self.lock = lock
        self.netmanager = ap_manager.netmanager
        self.clean = ap_manager.clean

        # Configuration paths
        self.conf_dir = self.config.get('conf_dir', ap_manager.config_manager.__bconfdir__)
        self.proc_dir = self.config['proc_dir']

    def has_running_instance(self) -> bool:
        """Check if there are any running instances"""
        self.lock.mutex_lock()
        try:
            for proc_item in os.listdir(self.proc_dir):
                pid_file = os.path.join(self.proc_dir, proc_item)
                if os.path.exists(pid_file):
                    with open(pid_file, 'r') as f:
                        pid = f.read().strip()
                    if os.path.exists(f'/proc/{pid}'):
                        return True
            return False
        finally:
            self.lock.mutex_unlock()

    def is_running_pid(self, pid: str) -> bool:
        """Check if a specific PID is running"""
        running = self.list_running()
        for entry in running:
            if entry.startswith(pid):
                return True
        return False

    def list_running_conf(self) -> List[str]:
        """List all running configuration directories"""
        self.lock.mutex_lock()

        try:
            running_confs = []
            for item in os.listdir(self.conf_dir):
                # all instance files have ap_manager prefix
                if item.endswith('.json') or 'ap_manager' not in item:
                    continue  # Skip json configs
                pid_file = os.path.join(self.proc_dir, item)
                wifi_iface_file = os.path.join(self.conf_dir, item.strip('.pid'), 'wifi_iface')

                if os.path.exists(pid_file) and os.path.exists(wifi_iface_file):
                    with open(pid_file, 'r') as f:
                        pid = f.read().strip()
                    if os.path.exists(f'/proc/{pid}'):
                        running_confs.append(os.path.join(self.conf_dir, item))  # Append the interface conf item
            return running_confs
        finally:
            self.lock.mutex_unlock()

    def list_running(self) -> List[str]:
        """List all running instances with their interfaces"""
        self.lock.mutex_lock()
        try:
            running_instances = []
            for conf in self.list_running_conf():
                iface = os.path.basename(conf)
                pid_file = os.path.join(self.proc_dir, iface)
                iface_file = os.path.join(conf, conf.strip('.pid'), 'wifi_iface')

                pid = None
                if os.path.exists(pid_file):
                    with open(pid_file, 'r') as f:
                        pid = f.read().strip()

                if os.path.exists(iface_file):
                    with open(os.path.join(conf, 'wifi_iface'), 'r') as f:
                        wifi_iface = f.read().strip()

                if (iface and wifi_iface) and iface == wifi_iface:
                    running_instances.append(f"{pid} {iface} ({wifi_iface})")
                # else:
                # running_instances.append(f"{pid} {iface} ({wifi_iface})")
            return running_instances
        finally:
            self.lock.mutex_unlock()

    def get_wifi_iface_from_pid(self, pid: str) -> Optional[str]:
        """Get the WiFi interface associated with a process ID"""
        running = self.list_running()
        for entry in running:
            parts = entry.split()
            if parts[0] == pid:
                # Return the last field (interface name)
                return parts[-1].rstrip(')')
        return None

    def get_pid_from_wifi_iface(self, wifi_iface: str) -> Optional[str]:
        """Get the process ID associated with a WiFi interface"""
        running = self.list_running()
        for entry in running:
            parts = entry.split()
            if wifi_iface in parts[-1]:
                return parts[0]
        return None

    def get_confdir_from_pid(self, pid: str) -> Optional[str]:
        """Get the configuration directory for a process ID"""
        self.lock.mutex_lock()
        try:
            for conf_dir in self.list_running_conf():
                pid_file = os.path.join(conf_dir, 'pid')
                if os.path.exists(pid_file):
                    with open(pid_file, 'r') as f:
                        if f.read().strip() == pid:
                            return conf_dir
            return None
        finally:
            self.lock.mutex_unlock()

    def send_stop_signal(self, pid_or_iface: str) -> None:
        """Send stop signal to a specific instance"""
        self.lock.mutex_lock()
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
            self.lock.mutex_unlock()

    def print_client(self, mac: str) -> None:
        """Print client information in a formatted way"""
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
        """List all clients connected to a specific instance"""
        wifi_iface = ""
        pid = ""

        # If argument is a PID, get the associated WiFi interface
        if pid_or_iface.isdigit():
            pid = pid_or_iface
            wifi_iface = self.get_wifi_iface_from_pid(pid)
            if not wifi_iface:
                sys.exit(f"Error: '{pid}' is not the PID of a running {self.ap_manager.prog_name} instance.")
        else:
            wifi_iface = pid_or_iface

        # Verify it's a WiFi interface
        if not self.ap_manager.is_wifi_interface(wifi_iface):
            sys.exit(f"Error: '{wifi_iface}' is not a WiFi interface.")

        # Get PID if not already set
        if not pid:
            pid = self.get_pid_from_wifi_iface(wifi_iface)
            if not pid:
                sys.exit(f"Error: '{wifi_iface}' is not used from {self.ap_manager.prog_name} instance.\n"
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
        sys.exit("Error: This option is not supported for the current driver.")

    def start_haveged_watchdog(self):
        """Start the haveged watchdog in a background thread"""
        from threading import Thread

        def haveged_watchdog():
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
                            self.lock.mutex_lock()
                            try:
                                # Start haveged with a specific PID file
                                subprocess.Popen(['sudo', 'haveged', '-w', '1024', '-p',
                                                  os.path.join(self.conf_dir, 'haveged.pid')])
                            finally:
                                self.lock.mutex_unlock()
                except (IOError, ValueError):
                    pass

                time.sleep(2)

        thread = Thread(target=haveged_watchdog, daemon=True)
        thread.start()
        return thread

    def is_haveged_installed(self):
        """Check if haveged is installed"""
        try:
            subprocess.run(['which', 'haveged'],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False

    def is_haveged_running(self):
        """Check if haveged is running (HAVE GEnerated Daemon)"""
        try:
            subprocess.run(['pidof', 'haveged'],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError:
            return False
