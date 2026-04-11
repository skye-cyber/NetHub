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
            with open(f"/sys/class/net/{iface}/mtu", "r") as f:
                return int(f.read().strip())
        except (IOError, ValueError):
            return None

    def is_interface_configured(self, iface=None) -> bool:
        """Check if the wireless interface is already configured as an AP.

        Returns:
            bool: True if the interface is configured as an AP, False otherwise
        """
        if not iface:
            iface = self.config["vwifi_iface"]

        try:
            # Check if the interface is up
            result = subprocess.run(
                ["ip", "link", "show", iface], capture_output=True, text=True
            )
            if "state UP" not in result.stdout:
                return False

            # Check if hostapd is already managing the interface
            result = subprocess.run(
                ["iw", "dev", iface, "info"], capture_output=True, text=True
            )
            if "type AP" in result.stdout:
                return True

            return False
        except Exception as e:
            print(f"Error checking interface configuration: {str(e)}")
            return False

    def is_dnsmasq_running(self) -> bool:
        return self.is_service_running(service="dnsmasq")

    def is_hostapd_running(self) -> bool:
        return self.is_service_running(service="hostapd")

    def is_service_running(self, service) -> bool:
        try:
            result = subprocess.run(["pidof", service], capture_output=True, text=True)

            if (
                result.stdout
                and int(result.stdout.split(" ")[0])
                and result.returncode == 0
            ):
                return True
            return False
        except Exception as e:
            print(f"Error checking dnsmasq status: {str(e)}")
            return False

    def kill_service(self, service) -> bool:
        try:
            result = subprocess.run(
                ["killall", service], capture_output=True, text=True
            )

            if (
                result.stdout
                and int(result.stdout.split(" ")[0])
                and result.returncode == 0
            ):
                return True
            return False
        except Exception as e:
            print(f"Error killing {service} status: {str(e)}")
            return False

    def start_service(self, service, restart=False) -> bool:
        try:
            cmd = (
                ["sudo", "systemctl", "start", service]
                if not restart
                else ["sudo", "systemctl", "restart", service]
            )

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("ap_manager UP")
                return True
            return False
        except Exception as e:
            print(f"Error starting {service} status: {str(e)}")
            return False

    def start_dnsmasq(self, config) -> bool:
        try:
            cmd = ["sudo", "dnsmasq", "--config-file", config]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("dnsmasq UP")
                return True
            return False
        except Exception as e:
            print(f"Error starting dnsmasq status: {str(e)}")
            return False

    def stop_service(self, service, restart=False) -> bool:
        try:
            cmd = ["sudo", "systemctl", "stop", service]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return True
            return False
        except Exception as e:
            print(f"Error starting {service} status: {str(e)}")
            return False

    def kill_dnsmasq(self) -> bool:
        return self.kill_service("dnsmasq")

    def kill_hostapd(self) -> bool:
        return self.kill_service("hostapd")

    def is_bridge_interface(self, iface=None) -> bool:
        """Check if interface is a bridge interface"""
        iface = iface if iface else self.config["vwifi_iface"]
        return os.path.exists(f"/sys/class/net/{iface}/bridge")

    def is_interface(self, iface=None):
        """Check if interface exists"""
        iface = iface if iface else self.config["vwifi_iface"]
        return os.path.exists(f"/sys/class/net/{iface}")

    def restart_hostapd(self) -> bool:
        return self.start_service(service="hostapd", restart=True)

    def get_hostapd_pid(self, pid_file=None):
        try:
            if os.path.exists(pid_file):
                with open(pid_file, "r") as f:
                    pid = f.read()
                    return pid
            return None
        except Exception as e:
            print(f"Error obtaining hostapd pid: {str(e)}: {pid_file}")
            return False


shared = Shared()
