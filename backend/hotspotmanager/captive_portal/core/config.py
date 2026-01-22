import json
from pathlib import Path
from typing import Dict, Any, Optional


class BaseConfig:
    """Base configuration class with shared settings"""

    # Shared configuration
    BASE_DIR = '/etc/ap_manager'
    GATEWAY = "192.168.100.1"
    SUBNET = "192.168.100.0/24"
    CAPTIVE_PORT = '8001'
    CLIENT_INTERFACE = 'xap0'
    INTERNET_INTERFACE = 'eth0'

    def __init__(self, config_file: Optional[str] = None, **kwargs):
        self._initialize_paths()
        self.config_file = config_file

        # Load configuration from file if provided
        self.config = self.load_from_json(config_file) if config_file else self.get_config()

        # Update with any additional kwargs
        if kwargs:
            self.update_config(**kwargs)

    def _initialize_paths(self):
        """Initialize all path-related attributes"""
        self.AUTH_DIR = Path(self.BASE_DIR) / 'auth'
        self.mac_file = self.AUTH_DIR / 'authenticated_macs'
        self.dnsmasq_config = Path("/etc/dnsmasq.d/ap_manager_portal.conf")
        self.dnsmasq_logfile = Path('/etc/ap_manager/dnsmasq.log')
        self.dnsmasq_leasefile = Path('/var/lib/misc/dnsmasq.leases')

    def get_config(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary"""
        return {
            'BASE_DIR': self.BASE_DIR,
            'GATEWAY': self.GATEWAY,
            'SUBNET': self.get_subnet(),
            'CAPTIVE_PORT': self.CAPTIVE_PORT,
            'CLIENT_INTERFACE': self.CLIENT_INTERFACE,
            'INTERNET_INTERFACE': self.INTERNET_INTERFACE,
            'AUTH_DIR': str(self.AUTH_DIR),
            'MAC_FILE': str(self.mac_file),
            'DNSMASQ_CONFIG': str(self.dnsmasq_config),
            'DNSMASQ_LOGFILE': str(self.dnsmasq_logfile),
            'DNSMASQ_LEASEFILE': str(self.dnsmasq_leasefile)
        }

    def update_config(self, **kwargs):
        """Update configuration values"""
        for key, value in kwargs.items():
            if key == 'vwifi_iface':
                self.CLIENT_INTERFACE = value
            if hasattr(self, key):
                setattr(self, key, value)
            elif hasattr(BaseConfig, key):
                setattr(BaseConfig, key, value)

    def _dict_update_config(self, new_config: dict) -> dict:
        self.config.update(**new_config)
        return self.config

    def load_from_json(self, config_file: str = None) -> bool:
        """Load configuration from JSON file"""
        if not config_file:
            config_file = self.config_file
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                self.update_config(**config_data)
            return config_data
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            print(f"Error loading config from {config_file}: {e}")
            return False

    def save_config(self):
        """Save configuration to file"""
        if not self.config_file:
            return False

        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

        return True

    def dump_to_json(self, config_file: str) -> bool:
        """Save current configuration to JSON file"""
        try:
            config_data = self.get_config()
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config to {config_file}: {e}")
            return False

    def get_broadcast_address(self) -> str:
        """Get broadcast address from gateway address"""
        return f"{'.'.join(self.GATEWAY.split('.')[:-1])}.255"

    def get_subnet(self) -> str:
        subnet = f"{self.GATEWAY.rsplit('.', 1)[0]}.0/24"
        self.SUBNET = subnet
        return subnet

    def get_dhcp_range(self) -> str:
        """Get DHCP range configuration"""
        return f"{self.SUBNET.split('/')[0].rsplit('.', 1)[0]}.10,{self.SUBNET.split('/')[0].rsplit('.', 1)[0]}.100,255.255.255.0,12h"

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BaseConfig':
        """Create BaseConfig instance from dictionary"""
        config = cls()
        config.update_config(**config_dict)
        return config


# Path(__file__).resolve().parent.parent / 'config/captive.json'

conf_file = Path('/etc/ap_manager/conf/captive.json')
baseconfig = BaseConfig(conf_file)
