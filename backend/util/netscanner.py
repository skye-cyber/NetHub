#!/usr/bin/env python3
import subprocess
import re
import logging
import time
from datetime import datetime
from devices.models import Device
from django.conf import settings

BASE_DIR = settings.BASE_DIR


class NetScanner:
    def __init__(self, subnet="192.168.12.0/24", interface="ap0"):
        self.subnet = subnet
        self.interface = interface
        self.authenticated_devices = Device.objects.all().values('mac_address').values_list()
        self.setup_logging()

    def setup_logging(self):
        # os.makedirs((BASE_DIR / "logs/captive").as_posix(), exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(BASE_DIR / "logs/device_scanner.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def get_connected_devices(self):
        """Get all connected devices using multiple methods"""
        devices = []
        is_set = False

        try:
            # Method 1: Use arp command
            result = subprocess.run(
                ["arp", "-a", "-i", self.interface],
                capture_output=True,
                text=True,
                check=True,
            )

            try:
                for line in result.stdout.split("\n"):
                    if self.interface in line and f"{self.subnet.rsplit('.', 1)}." in line:
                        subnet_parts = self.subnet.split('.')
                        # Parse: ? (192.168.12.100) at ab:cd:ef:12:34:56 [ether] on wlan0
                        ip_match = re.search(rf"\(({subnet_parts[0]}\.{subnet_parts[1]}\.{subnet_parts[2]}\.\d+)\)", line)
                        mac_match = re.search(r"at\s+([0-9a-fA-F:]{17})", line)

                        if ip_match and mac_match:
                            is_set = True
                            devices.append(
                                {
                                    "ip": ip_match.group(1),
                                    "mac": mac_match.group(1).lower(),
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )
            except Exception:
                pass

            if not is_set:
                # Method 2: Use ip neigh (more reliable)
                result = subprocess.run(
                    ["ip", "neigh", "show", "dev", self.interface],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                for line in result.stdout.split("\n"):
                    if self.subnet.rsplit('.', 1) in line and "REACHABLE" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            devices.append(
                                {
                                    "ip": parts[0],
                                    "mac": parts[4].lower(),
                                    "timestamp": datetime.now().isoformat(),
                                }
                            )

        except Exception as e:
            self.logger.error(f"Error scanning devices: {e}")

        return devices

    def scan_and_log(self):
        """Main scanning function"""
        self.logger.info("Starting device scan")

        devices = self.get_connected_devices()
        new_devices = []

        for device in devices:
            if device['mac'] in self.authenticated_devices:
                new_devices.append(device)
                self.logger.info(
                    f"New unauthenticated device: {device['ip']} - {device['mac']}"
                )
            else:
                self.logger.debug(
                    f"Authenticated device: {device['ip']} - {device['mac']}"
                )

        self.logger.info(
            f"Scan completed. Found {len(devices)} total devices, {len(new_devices)} new unauthenticated devices"
        )
        return new_devices

    def get_all_devices(self):
        return Device.objects.all().values('mac_address').values_list()

    def get_device_by_mac(self, mac):
        return Device.objects.filter(mac_address=mac) if mac else None


net_scanner = NetScanner()


def main():
    # Run continuous scanning
    while True:
        try:
            net_scanner.scan_and_log()
            time.sleep(3)  # Scan every 30 seconds
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Scanner error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
