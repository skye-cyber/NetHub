import os
import re
import subprocess
import time
from typing import Optional
from .lock import lock
from .shared import shared


class NetworkManager:
    def __init__(self, ap_man):
        # Global variables
        self.NM_OLDER_VERSION = False
        self.ADDED_UNMANAGED = set()
        self.NETWORKMANAGER_CONF = "/etc/NetworkManager/NetworkManager.conf"
        self.lock = lock
        self.ap_man = ap_man

    def _get_interface_freq_(self, iface=None) -> float:
        iface = iface if iface else self.ap_man.config['wifi_iface']
        result = subprocess.run(['iw', 'dev', iface, 'link'], check=True, capture_output=True, text=True)
        lines = result.stdout.split('\n')
        freq_line = [line for line in lines if 'freq' in line][0].strip()
        freq = float(freq_line.split(':', 1)[-1].strip())
        return freq

    def version_cmp(self, v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Returns:
            0 if v1 == v2
            1 if v1 < v2
            2 if v1 > v2
        """
        if not re.match(r'^[0-9]+(\.[0-9]+)*$', v1):
            raise ValueError("Wrong version format!")
        if not re.match(r'^[0-9]+(\.[0-9]+)*$', v2):
            raise ValueError("Wrong version format!")

        v1_parts = list(map(int, v1.split('.')))
        v2_parts = list(map(int, v2.split('.')))

        max_len = max(len(v1_parts), len(v2_parts))

        for i in range(max_len):
            v1_part = v1_parts[i] if i < len(v1_parts) else 0
            v2_part = v2_parts[i] if i < len(v2_parts) else 0

            if v1_part < v2_part:
                return 1
            elif v1_part > v2_part:
                return 2

        return 0

    def networkmanager_exists(self) -> bool:
        """Check if NetworkManager is installed and determine if it's an older version.

        Returns:
            bool: True if NetworkManager is installed, False otherwise
            Also sets NM_OLDER_VERSION global if version is checked successfully
        """
        try:
            # Check if nmcli exists
            subprocess.run(['which', 'nmcli'],
                           check=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)

            # Get NetworkManager version
            result = subprocess.run(['nmcli', '-v'],
                                    check=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True)

            # Extract version number
            nm_ver = re.search(r'[0-9]+(\.[0-9]+)*\.[0-9]+', result.stdout)
            if nm_ver:
                self.NM_OLDER_VERSION = self.version_cmp(nm_ver.group(0), "0.9.9") == 1
                return True

        except (subprocess.CalledProcessError, AttributeError):
            return False

        return False

    def networkmanager_is_running(self) -> bool:
        """Check if NetworkManager is running."""
        if not self.networkmanager_exists():
            return False

        try:
            if self.NM_OLDER_VERSION:
                result = subprocess.run(['nmcli', '-t', '-f', 'RUNNING', 'nm'],
                                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            else:
                result = subprocess.run(['nmcli', '-t', '-f', 'RUNNING', 'g'],
                                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return 'running' in result.stdout
        except subprocess.CalledProcessError:
            return False

    def networkmanager_knows_iface(self, iface: str) -> bool:
        """Check if the interface is known to NetworkManager."""
        try:
            result = subprocess.run(['nmcli', '-t', '-f', 'DEVICE', 'd'],
                                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return iface in result.stdout.splitlines()
        except subprocess.CalledProcessError:
            return False

    def networkmanager_iface_is_unmanaged(self, iface: str) -> bool:
        """Check if the interface is unmanaged by NetworkManager."""
        if not shared.is_interface(iface):
            return False

        if not self.networkmanager_knows_iface(iface):
            return True

        try:
            result = subprocess.run(['nmcli', '-t', '-f', 'DEVICE,STATE', 'd'],
                                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in result.stdout.splitlines():
                if line.startswith(f"{iface}:unmanaged"):
                    return True
            return False
        except subprocess.CalledProcessError:
            return False

    def networkmanager_add_unmanaged(self, iface: str, mac: Optional[str] = None) -> bool:
        """Add an interface to NetworkManager's unmanaged devices list."""
        # global self.ADDED_UNMANAGED

        if not self.networkmanager_exists():
            return False

        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.NETWORKMANAGER_CONF), exist_ok=True)

        # Create config file if it doesn't exist
        if not os.path.exists(self.NETWORKMANAGER_CONF):
            with open(self.NETWORKMANAGER_CONF, 'w'):
                pass

        # Get MAC address if not provided
        if self.NM_OLDER_VERSION and mac is None:
            mac = self.ap_man.get_macaddr(iface)
            if not mac:
                return False

        # Lock mutex
        try:
            # Read current unmanaged devices
            unmanaged = None
            with open(self.NETWORKMANAGER_CONF, 'r') as f:
                for line in f:
                    if line.startswith('unmanaged-devices='):
                        unmanaged = line.strip()
            was_empty = unmanaged is None
            if unmanaged:
                unmanaged = unmanaged.replace('unmanaged-devices=', '').replace(';', ' ').replace(',', ' ').split()

            # Check if already exists
            if unmanaged:
                target = f"mac:{mac}" if self.NM_OLDER_VERSION else f"interface-name:{iface}"
                if target in unmanaged:
                    return True

            # Add new entry
            if self.NM_OLDER_VERSION:
                new_entry = f"mac:{mac}"
            else:
                new_entry = f"interface-name:{iface}"

            if unmanaged:
                unmanaged.append(new_entry)
            else:
                unmanaged = [new_entry]

            # Format the unmanaged devices string
            unmanaged_str = ';'.join(unmanaged)
            unmanaged_line = f"unmanaged-devices={unmanaged_str}"

            # Update the config file
            with open(self.NETWORKMANAGER_CONF, 'r') as f:
                lines = f.readlines()

            with open(self.NETWORKMANAGER_CONF, 'w') as f:
                keyfile_found = False
                for line in lines:
                    if line.startswith('[keyfile]'):
                        keyfile_found = True
                    elif line.startswith('unmanaged-devices='):
                        continue
                    f.write(line)

                if not keyfile_found:
                    f.write("\n\n[keyfile]\n")
                elif was_empty:
                    f.write(f"{unmanaged_line}\n")
                else:
                    # Find the [keyfile] section and insert/update the unmanaged-devices line
                    in_keyfile = False
                    for line in lines:
                        if line.startswith('[keyfile]'):
                            in_keyfile = True
                        elif in_keyfile and line.startswith('['):
                            in_keyfile = False
                        if in_keyfile and line.startswith('unmanaged-devices='):
                            line = f"{unmanaged_line}\n"

            # Track added interfaces
            # Send SIGHUP to NetworkManager
            try:
                nm_pid = subprocess.run(['pidof', 'NetworkManager'],
                                        check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
                if nm_pid:
                    subprocess.run(['kill', '-HUP', nm_pid])
            except subprocess.CalledProcessError:
                pass

            return True
        finally:
            self.lock.mutex_unlock()

    def networkmanager_rm_unmanaged(self, iface: str, mac: Optional[str] = None) -> bool:
        """Remove an interface from NetworkManager's unmanaged devices list."""

        if not self.networkmanager_exists() or not os.path.exists(self.NETWORKMANAGER_CONF):
            return False

        # Get MAC address if not provided
        if self.NM_OLDER_VERSION and mac is None:
            mac = self.get_macaddr(iface)
            if not mac:
                return False

        # Lock mutex
        self.lock.mutex_lock()
        try:
            # Read current unmanaged devices
            unmanaged = None
            with open(self.NETWORKMANAGER_CONF, 'r') as f:
                for line in f:
                    if line.startswith('unmanaged-devices='):
                        unmanaged = line.strip()
                        break

            if not unmanaged:
                return False

            unmanaged = unmanaged.replace('unmanaged-devices=', '').replace(';', ' ').replace(',', ' ').split()

            # Remove the interface
            if self.NM_OLDER_VERSION:
                target = f"mac:{mac}"
            else:
                target = f"interface-name:{iface}"

            if target in unmanaged:
                unmanaged.remove(target)

            # Update the config file
            if not unmanaged:
                # Remove the unmanaged-devices line
                with open(self.NETWORKMANAGER_CONF, 'r') as f:
                    lines = f.readlines()

                with open(self.NETWORKMANAGER_CONF, 'w') as f:
                    for line in lines:
                        if not line.startswith('unmanaged-devices='):
                            f.write(line)
            else:
                # Update the unmanaged-devices line
                unmanaged_str = ';'.join(unmanaged)
                unmanaged_line = f"unmanaged-devices={unmanaged_str}"

                with open(self.NETWORKMANAGER_CONF, 'r') as f:
                    lines = f.readlines()

                with open(self.NETWORKMANAGER_CONF, 'w') as f:
                    for line in lines:
                        if line.startswith('unmanaged-devices='):
                            line = f"{unmanaged_line}\n"
                        f.write(line)

            # Remove from tracking set
            if iface in self.ADDED_UNMANAGED:
                self.ADDED_UNMANAGED.remove(iface)

            # Send SIGHUP to NetworkManager
            try:
                nm_pid = subprocess.run(['pidof', 'NetworkManager'],
                                        check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
                if nm_pid:
                    subprocess.run(['kill', '-HUP', nm_pid])
            except subprocess.CalledProcessError:
                pass

            return True
        except Exception:
            pass
        finally:
            self.lock.mutex_unlock()

    def networkmanager_fix_unmanaged(self) -> None:
        """Remove all unmanaged devices from NetworkManager configuration."""
        if not os.path.exists(self.NETWORKMANAGER_CONF):
            return

        self.mutex_lock()
        try:
            with open(self.NETWORKMANAGER_CONF, 'r') as f:
                lines = f.readlines()

            with open(self.NETWORKMANAGER_CONF, 'w') as f:
                for line in lines:
                    if not line.startswith('unmanaged-devices='):
                        f.write(line)

            # Send SIGHUP to NetworkManager
            try:
                nm_pid = subprocess.run(['pidof', 'NetworkManager'],
                                        check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
                if nm_pid:
                    subprocess.run(['kill', '-HUP', nm_pid])
            except subprocess.CalledProcessError:
                pass
        finally:
            self.lock.mutex_unlock()

    def networkmanager_rm_unmanaged_if_needed(self, iface: str, mac: Optional[str] = None) -> bool:
        """Remove an interface from unmanaged list if it was added by this script."""
        if iface in self.ADDED_UNMANAGED:
            return self.networkmanager_rm_unmanaged(iface, mac)
        return False

    def networkmanager_wait_until_unmanaged(self, iface: str, timeout: int = 30) -> bool:
        """Wait until the interface is marked as unmanaged by NetworkManager."""
        print(f"Wait for {iface} to be unmanaged")
        if not self.networkmanager_is_running():
            return False

        # self.networkmanager_add_unmanaged(iface)
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.networkmanager_iface_is_unmanaged(iface)
            if result:
                return True
            if not shared.is_interface(iface):
                raise RuntimeError(f"Interface '{iface}' does not exist. "
                                   "It's probably renamed by a udev rule.")
            time.sleep(1)

        return False

    def rfkill_off(self, iface='wlan'):
        try:
            return subprocess.run(['sudo', 'rfkill', 'unblock', 'wlan'], check=True)
        except Exception:
            return False

    def wifi_switch(self, state="off"):
        try:
            return subprocess.run(['sudo', 'nmcli', 'r', 'wifi', state], check=True)
        except Exception:
            return False

    def kill_hostapd(self):
        try:
            return subprocess.run(['sudo', 'killall', 'hostapd'], stdout=subprocess.PIPE, error=subprocess.PIPE, check=True)
        except Exception:
            return False


netmanager = NetworkManager(ap_man=None)
