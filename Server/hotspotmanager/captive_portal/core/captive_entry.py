from .start import startcaptive
from .stop import stopcaptive
from .config import BaseConfig
from .firewall import firewall
from .setup import captivesetup
from typing import Dict, Any, Optional, List
import subprocess
from ap_utils.colors import fg


class Captive:
    def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
        """Initialize Captive portal with optional configuration"""
        self.config = config if config else BaseConfig(**kwargs)
        self.firewall = firewall
        self.setup = captivesetup

    def start(self):
        """Start the captive portal service"""
        return startcaptive.start()

    def stop(self):
        """Stop the captive portal service"""
        return stopcaptive.stop()

    def status(self) -> Dict[str, Any]:
        """Get current status of captive portal"""
        status_info = {
            "running": self._is_running(),
            "config": self.config.get_config(),
            "authenticated_devices": self._get_authenticated_devices(),
            "firewall_rules": self._get_firewall_status(),
        }
        return status_info

    def monitor(self) -> bool:
        """Monitor captive portal activity"""
        print("Monitoring captive portal...")
        self.firewall.verify_chains()
        return True

    def check(self) -> bool:
        """Check captive portal connectivity"""
        print("Checking captive portal connectivity...")
        try:
            # Check if gateway is reachable
            result = subprocess.run(
                ["ping", "-c", "1", self.config.GATEWAY], capture_output=True, text=True
            )

            if result.returncode == 0:
                print(f"Gateway {self.config.GATEWAY} is reachable")
                return True
            else:
                print(f"Gateway {self.config.GATEWAY} is not reachable")
                return False
        except Exception as e:
            print(f"Error checking connectivity: {e}")
            return False

    def test(self) -> bool:
        """Test captive portal configuration"""
        print("Testing captive portal configuration...")
        try:
            # Test DNS resolution
            subprocess.run(["nslookup", "google.com", self.config.GATEWAY], check=True)

            # Test firewall rules
            self.firewall.verify_chains()

            print("Captive portal configuration test passed")
            return True
        except Exception:
            print("Test failed")
            return False

    def debug(self) -> bool:
        """Debug captive portal issues"""
        print("Debugging captive portal...")

        # Show current configuration
        print(f"\n{fg.BLUE}Current Configuration:{fg.RESET}")
        for key, value in self.config.get_config().items():
            print(f"  {key}: {value}")

        # Show firewall status
        print(f"\n{fg.GREEN}Firewall Status:{fg.RESET}")
        self.firewall.verify_chains()

        # Verbose debug
        print(f"\n{fg.BWHITE}Verborse debug info:{fg.RESET}")
        self.firewall.verify_chains_verbose()

        # Show authenticated devices
        print(f"\n{fg.LBLUE}Authenticated Devices:{fg.RESET}")
        auth_devices = self._get_authenticated_devices()
        if auth_devices:
            for device in auth_devices:
                print(f"  - {device}")
        else:
            print(f"  {fg.FWHITE}No authenticated devices{fg.RESET}")

        return True

    def reset(self) -> bool:
        """Reset captive portal to default state"""
        print("Resetting captive portal...")

        # Stop services
        self.stop()

        # Clear firewall rules
        self.firewall.clear_iptables()

        # Reset configuration to defaults
        self.config = BaseConfig()

        # Clean up authenticated devices
        if self.config.mac_file.exists():
            self.config.mac_file.write_text("")

        print("Captive portal reset complete")
        return True

    def update_config(self, config_file: Optional[str] = None, **kwargs) -> bool:
        """Update captive portal configuration"""
        if config_file:
            return self.config.load_from_json(config_file)
        elif kwargs:
            self.config.update_config(**kwargs)
            return True
        return False

    def save_config(self, config_file: str) -> bool:
        """Save current configuration to file"""
        return self.config.save_to_json(config_file)

    def add_authenticated_device(self, mac_address: str) -> bool:
        """Add a device to authenticated list"""
        try:
            with open(self.config.mac_file, "a") as f:
                f.write(f"{mac_address}\n")

            # Update firewall rules
            self.firewall.update([mac_address])
            return True
        except Exception as e:
            print(f"Error adding authenticated device: {e}")
            return False

    def remove_authenticated_device(self, mac_address: str) -> bool:
        """Remove a device from authenticated list"""
        try:
            current_devices = self._get_authenticated_devices()
            if mac_address in current_devices:
                current_devices.remove(mac_address)
                with open(self.config.mac_file, "w") as f:
                    f.write("\n".join(current_devices) + "\n")

                # Update firewall rules
                self.firewall.update(current_devices)
                return True
            return False
        except Exception as e:
            print(f"Error removing authenticated device: {e}")
            return False

    def _is_running(self) -> bool:
        """Check if captive portal is running"""
        try:
            # Check if dnsmasq is running
            result = subprocess.run(
                ["service", "dnsmasq", "status"], capture_output=True, text=True
            )

            return result.returncode == 0
        except Exception:
            return False

    def _get_authenticated_devices(self) -> List[str]:
        """Get list of authenticated devices"""
        if self.config.mac_file.exists():
            with open(self.config.mac_file, "r") as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        return []

    def _get_firewall_status(self) -> Dict[str, Any]:
        """Get firewall status information"""
        try:
            # Count existing MAC rules
            mac_count = self.firewall.get_existing()

            return {"mac_rules": mac_count, "chains_configured": True}
        except Exception:
            return {"mac_rules": 0, "chains_configured": False}

    @property
    def properties(self) -> Dict[str, Any]:
        """Get captive portal properties"""
        return {
            "config": self.config.get_config(),
            "status": self.status(),
            "authenticated_devices": self._get_authenticated_devices(),
        }
