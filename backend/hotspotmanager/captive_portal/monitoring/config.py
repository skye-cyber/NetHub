# ==================== Configuration ====================

from pathlib import Path


class Config:
    BASE_DIR = Path("/etc/ap_manager")
    AUTH_FILE = BASE_DIR / "auth" / "authenticated_macs"
    INTERFACE = "xap0"
    SUBNET = "192.168.100.0/24"
    API_ENDPOINT = "http://localhost:8001/api/devices/"  # Django API endpoint
    USE_API = False  # Set to True when API is ready
    SCAN_INTERVAL = 10  # seconds
    DNS_SERVER = "192.168.100.1"  # Local DNS for reverse lookup
