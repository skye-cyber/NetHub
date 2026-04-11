# ==================== Device Data Model ====================
from datetime import datetime


class Device:
    def __init__(self, ip: str, mac: str, authenticated: bool = False, state: str = 'Unkown'):
        self.ip = ip
        self.mac = mac.lower()
        self.authenticated = authenticated
        self.state = state
        self.hostname = None
        self.vendor = None
        self.first_seen = datetime.now()
        self.last_seen = datetime.now()
        self.traffic_rx = 0
        self.traffic_tx = 0
        self.connection_time = 0

    def update(self):
        self.last_seen = datetime.now()

    def __repr__(self):
        return f"Device(ip={self.ip}, mac={self.mac}, auth={self.authenticated}, state={self.state})"
