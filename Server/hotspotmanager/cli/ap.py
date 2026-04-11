from pathlib import Path
from typing import Optional
from rich.console import Console

from core.ap_manager import ApManager
from ap_utils.config import ConfigManager
from captive_portal.core.captive_entry import Captive
from captive_portal.core.config import BaseConfig

console = Console()


class APManagerCLI:
    """Main CLI controller"""

    def __init__(self):
        self.manager = ApManager()
        self.config_manager = None
        self.captive = None

    def load_config(self, config_file: Optional[str] = None):
        """Load configuration"""
        if config_file and Path(config_file).exists():
            self.config_manager = ConfigManager(config_file)
        else:
            self.config_manager = ConfigManager()

        # Initialize captive portal with config
        self.captive = Captive(BaseConfig(config_file=config_file))

    def update_config(self, **kwargs):
        """Update configuration with provided values"""
        if not self.config_manager:
            self.load_config()

        # Filter out None values
        updates = {k: v for k, v in kwargs.items() if v is not None}

        if updates:
            # Update main config
            self.config_manager._dict_update(self.config_manager.get_config, updates)
            self.config_manager.save_config()

            # Update hostapd config if relevant keys
            hostapd_keys = {'ssid', 'password', 'channel', 'wpa_version', 'hidden'}
            if any(k in hostapd_keys for k in updates):
                hostman = ConfigManager(self.config_manager.__bconfdir__ / 'hostapd.json')
                hostman._dict_update(None, updates)
                hostman.save_config()

            # Update network config if relevant keys
            network_keys = {'wifi_iface', 'internet_iface', 'gateway', 'share_method'}
            if any(k in network_keys for k in updates):
                netman = ConfigManager(self.config_manager.__bconfdir__ / 'netconf.json')
                netman._dict_update(None, updates)
                netman.save_config()

            console.print("[green]✓ Configuration updated[/green]")
