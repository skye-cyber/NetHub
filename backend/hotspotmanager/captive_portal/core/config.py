from pathlib import Path
from typing import Dict, Any


class BaseConfig:
    """Base configuration class with shared settings"""

    # Shared configuration
    BASE_DIR = '/etc/ap_manager'
    GATEWAY_ADDRESS = "192.168.100.1"
    SUBNET = "192.168.100.0/24"
    CAPTIVE_PORT = '8888'
    CLIENT_INTERFACE = 'xap0'
    INTERNET_INTERFACE = 'eth0'

    def __init__(self):
        self._initialize_paths()

    def _initialize_paths(self):
        """Initialize all path-related attributes"""
        self.AUTH_DIR = Path(self.BASE_DIR) / 'auth'
        self.mac_file = self.AUTH_DIR / 'authenticated_macs'
        self.dnsmasq_config = Path("/etc/dnsmasq.d/ap_manager_portal.conf")
        self.dnsmasq_logfile = Path('/etc/ap_manager/dnsmasq.log')
        self.dnsmasq_leasefile = Path('/var/lib/misc/dnsmasq.leases')

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as a dictionary"""
        return {
            'BASE_DIR': cls.BASE_DIR,
            'GATEWAY_ADDRESS': cls.GATEWAY_ADDRESS,
            'SUBNET': cls.SUBNET,
            'CAPTIVE_PORT': cls.CAPTIVE_PORT,
            'CLIENT_INTERFACE': cls.CLIENT_INTERFACE,
            'INTERNET_INTERFACE': cls.INTERNET_INTERFACE,
            'AUTH_DIR': cls.BASE_DIR / 'auth',
            'MAC_FILE': (cls.BASE_DIR / 'auth') / 'authenticated_macs'
        }

    @classmethod
    def update_config(cls, **kwargs):
        """Update configuration values"""
        for key, value in kwargs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
