# ==================== Backend Data Sources ====================
from pathlib import Path
from typing import List, Optional
from .writer import writer

# Try to import requests for API calls, fallback to file
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class DataSource:
    """Abstract base class for data sources"""

    def get_authenticated_macs(self) -> List[str]:
        raise NotImplementedError

    def authenticate_device(self, mac: str) -> bool:
        raise NotImplementedError

    def block_device(self, mac: str) -> bool:
        raise NotImplementedError


class FileDataSource(DataSource):
    """File-based data source (current implementation)"""

    def __init__(self, auth_file: Path):
        self.auth_file = auth_file
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        self.auth_file.touch(exist_ok=True)

    def get_authenticated_macs(self) -> List[str]:
        """Read authenticated MACs from file"""
        writer.write("Auth devices")
        try:
            with open(self.auth_file, 'r') as f:
                dev = [line.strip().lower() for line in f if line.strip()]
                writer.write(f"Devices:\n{dev}\nRead:\n{f.readlines()}")

                return dev
        except Exception:
            return []

    def authenticate_device(self, mac: str) -> bool:
        """Add MAC to authenticated file"""
        try:
            mac = mac.lower()
            auth_macs = self.get_authenticated_macs()
            if mac not in auth_macs:
                with open(self.auth_file, 'a') as f:
                    f.write(f"{mac}\n")
                return True
            return False
        except Exception:
            return False

    def block_device(self, mac: str) -> bool:
        """Remove MAC from authenticated file"""
        try:
            mac = mac.lower()
            auth_macs = self.get_authenticated_macs()
            if mac in auth_macs:
                with open(self.auth_file, 'w') as f:
                    for auth_mac in auth_macs:
                        if auth_mac != mac:
                            f.write(f"{auth_mac}\n")
                return True
            return False
        except Exception:
            return False


class APIDataSource(DataSource):
    """API-based data source (for future Django integration)"""

    def __init__(self, api_endpoint: str, api_key: Optional[str] = None):
        self.api_endpoint = api_endpoint.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session() if HAS_REQUESTS else None

    def get_authenticated_macs(self) -> List[str]:
        """Fetch authenticated MACs from API"""
        if not self.session:
            return []

        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"

            response = self.session.get(
                f"{self.api_endpoint}/authenticated/",
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return [device['mac'].lower() for device in data.get('devices', [])]
        except Exception:
            pass

        return []

    def authenticate_device(self, mac: str) -> bool:
        """Authenticate device via API"""
        if not self.session:
            return False

        try:
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"

            response = self.session.post(
                f"{self.api_endpoint}/authenticate/",
                json={'mac': mac.lower()},
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def block_device(self, mac: str) -> bool:
        """Block device via API"""
        if not self.session:
            return False

        try:
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"

            response = self.session.post(
                f"{self.api_endpoint}/block/",
                json={'mac': mac.lower()},
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
