import re

stdout = """192.168.100.48 lladdr aa:77:15:e0:98:09 STALE
 fe80::a877:15ff:fee0:9809 lladdr aa:77:15:e0:98:09 STALE"""


def is_valid_ip(ip: str) -> bool:
    ip_match = re.search(r'[0-9]+[\.0-9]*', ip).group(0)
    return ip_match and len(ip_match.split('.')) >= 4


def _is_valid_mac(mac: str) -> bool:
    """Validate MAC address format"""
    import re
    mac_pattern = re.compile(r'^([0-9a-f]{2}[:-]){5}([0-9a-f]{2})$', re.IGNORECASE)
    return bool(mac_pattern.match(mac))

for line in stdout.strip().split('\n'):
    if line:
        parts = line.split()
        print(parts)
        if len(parts) >= 4:
            ip = parts[0]
            mac = parts[2]
            if is_valid_ip(ip) and _is_valid_mac(mac):
                print(ip, mac)
