import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigManager:
    def __init__(self, config_file: dict = BASE_DIR / 'config/config.json'):
        self.config_file = config_file
        self.config = self.load_config()

    @property
    def get_config(self):
        return self.config

    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                # self.config = {**self.default_config, **user_config}
        else:
            raise Exception(f"Config file not found {self.config_file}")
        return self.config

    def update_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    @property
    def __str__(self):
        return '\n'.join(f"{k}={v}" for k, v in self.config.items()).strip() if self.config else None

    def _dict_update(self, d1: dict, d2: dict):
        """
        Args:
            d1: dictionary to update - target dict
            d2: dictionary to update from - source dict
        """
        if not d1:
            d1 = self.config

        return d1.update({k.lower(): v for k, v in d2.items() if v and k in config_manager.config.keys()}) if d1 and d2 else d1 or {}

    @property
    def __bdir__(self):
        return BASE_DIR

    @property
    def __bconfdir__(self):
        return BASE_DIR / 'config'


config_manager = ConfigManager()
