import socket
import subprocess
import requests
import logging
import re
from typing import Dict, Optional, List
from dataclasses import dataclass
import platform
# import scapy.all as scapy
# from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class RemoteDeviceMetadata:
    """Data class to store remote device metadata"""
    ip_address: str
    mac_address: str
    hostname: str
    operating_system: str
    open_ports: List[int]
    services: Dict[str, str]
    manufacturer: str
    network_distance: str
    response_time: float
    user_agent: str
    additional_info: Dict


class DeviceUtil:
    """
    A robust class for obtaining remote device metadata including hostname,
    operating system, user agent, and other related information
    """

    def __init__(self, log_level=logging.INFO):
        self.logger = self._setup_logging(log_level)
        self.session = requests.Session()
        self.common_ports = [21, 22, 23, 25, 53, 80, 110, 443, 993, 995, 3389, 8080]
        self.os_fingerprints = self._load_os_fingerprints()

    def _setup_logging(self, level: int) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        logger.setLevel(level)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_os_fingerprints(self) -> Dict:
        """Load OS fingerprinting patterns"""
        return {
            'Windows': {
                'ttl_range': (128, 128),
                'tcp_flags': ['SYN', 'ACK'],
                'common_ports': [135, 139, 445, 3389]
            },
            'Linux': {
                'ttl_range': (64, 64),
                'tcp_flags': ['SYN', 'ACK'],
                'common_ports': [22, 111, 631]
            },
            'macOS': {
                'ttl_range': (64, 64),
                'tcp_flags': ['SYN', 'ACK'],
                'common_ports': [22, 548, 62078]
            },
            'Router': {
                'ttl_range': (255, 255),
                'tcp_flags': ['SYN', 'ACK'],
                'common_ports': [23, 80, 443, 8291]
            }
        }

    def get_hostname_from_ip(self, ip_address: str) -> str:
        """Resolve hostname from IP address using DNS reverse lookup"""
        try:
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            return hostname
        except (socket.herror, socket.gaierror):
            self.logger.warning(f"Could not resolve hostname for {ip_address}")
            return "Unknown"
        except Exception as e:
            self.logger.error(f"Error in hostname resolution: {e}")
            return "Unknown"

    def get_mac_address(self, ip_address: str) -> Optional[str]:
        """Get MAC address using ARP lookup"""
        try:
            mac = self.get_client_mac(ip_address)

            return mac if mac else (self._get_mac_windows(ip_address)
                                    if platform.system().lower() == "windows"
                                    else self._get_mac_linux(ip_address)
                                    )
        except Exception as e:
            self.logger.error(f"Error getting MAC address: {e}")
            return None

    def _get_mac_windows(self, ip_address: str) -> Optional[str]:
        """Get MAC address on Windows systems"""
        try:
            result = subprocess.run(
                f"arp -a {ip_address}",
                capture_output=True,
                text=True,
                shell=True
            )

            for line in result.stdout.split('\n'):
                if ip_address in line:
                    mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                    if mac_match:
                        return mac_match.group(0)
            return None
        except Exception as e:
            self.logger.error(f"Windows ARP lookup failed: {e}")
            return None

    def _get_mac_linux(self, ip_address: str) -> Optional[str]:
        """Get MAC address on Linux systems"""
        try:
            result = subprocess.run(
                f"arp -n {ip_address}",
                capture_output=True,
                text=True,
                shell=True
            )

            for line in result.stdout.split('\n'):
                if ip_address in line:
                    parts = line.split()
                    for part in parts:
                        if re.match(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', part):
                            return part
            return None
        except Exception as e:
            self.logger.error(f"Linux ARP lookup failed: {e}")
            return None

    def get_manufacturer_from_mac(self, mac_address: str) -> str:
        """Get manufacturer information from MAC address OUI"""
        try:
            if not mac_address:
                return 'UNKNOWN'
            # Clean MAC address
            mac_clean = mac_address.replace(':', '').replace('-', '').upper()[:6]

            # Try multiple MAC vendor APIs
            vendors = [
                f"https://api.macvendors.com/{mac_clean}",
                f"https://macaddress.io/api/v1?apiKey=YOUR_API_KEY&output=json&search={mac_clean}"
            ]

            for vendor_url in vendors:
                try:
                    response = self.session.get(vendor_url, timeout=5)
                    if response.status_code == 200:
                        return response.text.strip()
                except Exception:
                    continue

            # Fallback to local OUI database
            return self._local_oui_lookup(mac_clean)

        except Exception as e:
            self.logger.error(f"Error getting manufacturer: {e}")
            return "Unknown Manufacturer"

    def get_client_mac(self, ip_address):
        """Get MAC address from IP using ARP table"""
        try:
            # Try to get MAC from ARP table
            result = subprocess.run(
                ["arp", "-n", ip_address], capture_output=True, text=True, check=True
            )

            # Parse MAC address from ARP output
            mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", result.stdout)
            if mac_match:
                return mac_match.group().lower()

            # If not in ARP table, try to ping and check again
            subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip_address], capture_output=True, check=False
            )

            result = subprocess.run(
                ["arp", "-n", ip_address], capture_output=True, text=True, check=True
            )
            mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", result.stdout)

            return mac_match.group().lower() if mac_match else None

        except Exception as e:
            print(f"Error getting MAC address: {e}")
            return None

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def _local_oui_lookup(self, mac_prefix: str) -> str:
        """Local OUI database lookup as fallback"""
        oui_database = {
            '000C29': 'VMware',
            '001C14': 'Cisco',
            '0050F2': 'Microsoft',
            '001122': 'Cisco',
            '00163E': 'Cisco',
            '001B21': 'Cisco',
            '001C0E': 'Cisco',
            '001F6B': 'Cisco',
            '0021A8': 'Cisco',
            '002436': 'Cisco',
            '0025BC': 'Cisco',
            '14CC20': 'Cisco',
            '18A9F8': 'Cisco',
            '1C1AC0': 'Cisco',
            '1C1B68': 'Cisco',
            '283CE4': 'Cisco',
            '3C970E': 'Cisco',
            '3CB15B': 'Cisco',
            '3CB72B': 'Cisco',
            '3CB87A': 'Cisco',
            '3CBBFD': 'Cisco',
            '3CC1F6': 'Cisco',
            '3CD0F8': 'Cisco',
            '40F2E9': 'Cisco',
            '443839': 'Cisco',
            '4C60DE': 'Cisco',
            '5C0A5B': 'Cisco',
            '6C2056': 'Cisco',
            '6C416A': 'Cisco',
            '6CF373': 'Cisco',
            '78BC1A': 'Cisco',
            '885395': 'Cisco',
            '9C1D58': 'Cisco',
            'A4B1E9': 'Cisco',
            'A89D21': 'Cisco',
            'B41489': 'Cisco',
            'B83861': 'Cisco',
            'BC16F5': 'Cisco',
            'BC67AB': 'Cisco',
            'C0335E': 'Cisco',
            'C83D97': 'Cisco',
            'CC46D6': 'Cisco',
            'DCA5F4': 'Cisco',
            'E8B748': 'Cisco',
            'F87B20': 'Cisco',
            'FC45C4': 'Cisco',
            '001C23': 'Cisco',
            '001D45': 'Cisco',
            '001E13': 'Cisco',
            '001E4A': 'Cisco',
            '001E7D': 'Cisco',
            '001F9C': 'Cisco',
            '0021D8': 'Cisco',
            '0023EB': 'Cisco',
            '00255E': 'Cisco',
            '0026F2': 'Cisco',
            '0026F3': 'Cisco',
            '54724F': 'Cisco',
            'C8D719': 'Cisco',
            'F87B8C': 'Cisco',
            'FC4DD4': 'Cisco',
            'FCE998': 'Cisco',
            '000E38': 'Cisco',
            '0012F2': 'Cisco',
            '00142B': 'Cisco',
            '0015F2': 'Cisco',
            '0016C4': 'Cisco',
            '0016F6': 'Cisco',
            '0017DF': 'Cisco',
            '00183F': 'Cisco',
            '0018B9': 'Cisco',
            '0019A6': 'Cisco',
            '0019E2': 'Cisco',
            '0019E3': 'Cisco',
            '001B0D': 'Cisco',
            '001B2A': 'Cisco',
            '001BD4': 'Cisco',
            '001C0F': 'Cisco',
            '001C57': 'Cisco',
            '001D70': 'Cisco',
            '001E49': 'Cisco',
            '001F6C': 'Cisco',
            '001FF3': 'Cisco',
            '0021A1': 'Cisco',
            '0021F2': 'Cisco',
            '0022BD': 'Cisco',
            '0022FC': 'Cisco',
            '0023BD': 'Cisco',
            '0023EB': 'Cisco',
            '0024F7': 'Cisco',
            '0024FC': 'Cisco',
            '00255E': 'Cisco',
            '0025BC': 'Cisco',
        }
        return oui_database.get(mac_prefix, 'UNKOWN')


meta_scanner = DeviceUtil()
