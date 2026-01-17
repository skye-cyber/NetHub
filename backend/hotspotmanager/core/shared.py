import os


class Shared:
    def __init__(self):
        pass

    def get_mtu(self, iface):
        """Get MTU of an interface"""
        if not self.is_interface(iface):
            return None
        try:
            with open(f"/sys/class/net/{iface}/mtu", 'r') as f:
                return int(f.read().strip())
        except (IOError, ValueError):
            return None

    def is_interface(self, iface):
        """Check if interface exists"""
        return os.path.exists(f"/sys/class/net/{iface}")


shared = Shared()
