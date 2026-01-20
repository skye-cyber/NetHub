import os
import subprocess


class Shared:
    def __init__(self):
        pass

    def get_mtu(self, iface):
        """Get MTU of an interface"""
        if not self.is_interface(iface):
            return None
        try:
            with open(f"/sys/class/net/{iface}/mtu", 'r') as f:
                return int(f.read().strip())
        except (IOError, ValueError):
            return None

    def is_interface_configured(self, iface=None) -> bool:
        """Check if the wireless interface is already configured as an AP.

        Returns:
            bool: True if the interface is configured as an AP, False otherwise
        """
        if not iface:
            iface = self.config['vwifi_iface']

        try:
            # Check if the interface is up
            result = subprocess.run(['ip', 'link', 'show', iface],
                                    capture_output=True, text=True)
            if "state UP" not in result.stdout:
                return False

            # Check if hostapd is already managing the interface
            result = subprocess.run(['iw', 'dev', iface, 'info'],
                                    capture_output=True, text=True)
            if "type AP" in result.stdout:
                return True

            return False
        except Exception as e:
            print(f"Error checking interface configuration: {str(e)}")
            return False

    def is_dnsmasq_running(self) -> bool:
        try:
            result = subprocess.run(['pidof', 'dnsmasq'],
                                    capture_output=True, text=True)

            print(result.stdout)

            if result.stdout and int(result.stdout.split(' ')[0]) and result.returncode == 0:
                return True
            return False
        except Exception as e:
            print(f"Error checking dnsmasq status: {str(e)}")
            return False

    def kill_dnsmasq(self) -> bool:
        try:
            result = subprocess.run(['killall', 'dnsmasq'],
                                    capture_output=True, text=True)
            # Restart
            subprocess.run(['sudo', 'systemctl', 'restart', 'dnsmasq'],
                           capture_output=True, text=True)

            print(result.stdout)

            if result.returncode == 0:
                return True
            return False
        except Exception as e:
            print(f"Error killing dnsmasq status: {str(e)}")
            return False

    def is_bridge_interface(self, iface=None) -> bool:
        """Check if interface is a bridge interface"""
        iface = iface if iface else self.config['vwifi_iface']
        return os.path.exists(f"/sys/class/net/{iface}/bridge")

    def is_interface(self, iface=None):
        """Check if interface exists"""
        iface = iface if iface else self.config['vwifi_iface']
        return os.path.exists(f"/sys/class/net/{iface}")


shared = Shared()
