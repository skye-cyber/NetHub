import subprocess
from typing import Optional
from .config import BaseConfig


class CaptiveSetup:
    def __init__(self, config: Optional[BaseConfig] = BaseConfig()):
        self.config = config if config else BaseConfig()

        # Initialize attributes from config
        self.client_interface = self.config.CLIENT_INTERFACE
        self.internet_interface = self.config.INTERNET_INTERFACE
        self.BASE_DIR = self.config.BASE_DIR
        self.gateway_address = self.config.GATEWAY_ADDRESS
        self.captive_port = self.config.CAPTIVE_PORT
        self.AUTH_DIR = self.config.AUTH_DIR
        self.mac_file = self.config.mac_file

        self.init_files()

    def setup(self) -> bool:
        """Setup captive portal configuration"""
        try:
            self.enable_ip_forwarding()
            self.clear_rules()
            self.create_chains()
            self.add_default_rules()
            self.configure_basic_forwarding_rules()
            self.add_nat_rules()
            self.add_portal_chain_rules()
            self.add_nat_masquerade_rule()
            self.add_input_rules()

            print("Captive portal setup complete")
            print(f"Gateway IP: {self.gateway_address}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error during setup: {e}")
            return False

    def init_files(self) -> bool:
        """Initialize necessary directories and files"""
        try:
            self.AUTH_DIR.mkdir(parents=True, exist_ok=True)
            self.mac_file.touch(exist_ok=True)
            return True
        except PermissionError:
            return False

    def clear_rules(self) -> bool:
        """Clear existing iptables rules"""
        try:
            subprocess.run(["iptables", "-F"], check=True)
            subprocess.run(["iptables", "-t", "nat", "-F"], check=True)
            subprocess.run(["iptables", "-X"], check=True)
            subprocess.run(["iptables", "-t", "nat", "-X"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error clearing iptables rules: {e}")
            return False

    def add_default_rules(self) -> bool:
        """Set default iptables policies"""
        try:
            subprocess.run(["iptables", "-P", "INPUT", "ACCEPT"], check=True)
            subprocess.run(["iptables", "-P", "FORWARD", "DROP"], check=True)
            subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error setting default rules: {e}")
            return False

    def enable_ip_forwarding(self) -> bool:
        """Enable IP forwarding"""
        try:
            with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
                f.write('1')
            return True
        except IOError as e:
            print(f"Error enabling IP forwarding: {e}")
            return False

    def create_chains(self) -> bool:
        """Create necessary iptables chains"""
        print("Creating chains")
        try:
            # Create CAPTIVE_PORTAL chain if it doesn't exist
            subprocess.run(["iptables", "-N", "CAPTIVE_PORTAL"], check=True)

            # Flush the chain if it exists
            subprocess.run(["iptables", "-F", "CAPTIVE_PORTAL"], check=True)

            # Create AUTH_REDIRECT chain if it doesn't exist
            subprocess.run(["iptables", "-t", "nat", "-N", "AUTH_REDIRECT"], check=True)

            # Flush the chain if it exists
            subprocess.run(["iptables", "-t", "nat", "-F", "AUTH_REDIRECT"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating chains: {e}")
            return False

    def configure_basic_forwarding_rules(self) -> bool:
        """Configure basic forwarding rules"""
        print("Setting basic forwarding rules")
        try:
            # Allow established connections
            subprocess.run([
                "iptables", "-A", "FORWARD", "-i", self.internet_interface,
                "-o", self.client_interface, "-m", "state",
                "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"
            ], check=True)

            # Allow access to gateway
            subprocess.run([
                "iptables", "-A", "FORWARD", "-i", self.client_interface,
                "-d", self.gateway_address, "-j", "ACCEPT"
            ], check=True)

            # Allow DNS queries
            subprocess.run([
                "iptables", "-A", "FORWARD", "-i", self.client_interface,
                "-o", self.internet_interface, "-p", "udp", "--dport", 53,
                "-j", "ACCEPT"
            ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error configuring basic forwarding rules: {e}")
            return False

    def add_nat_rules(self) -> bool:
        """Add NAT redirect rules"""
        print("Setting NAT redirect rules")
        try:
            # Clear NAT rules
            subprocess.run(["iptables", "-t", "nat", "-F", "PREROUTING"], check=True)

            # Redirect HTTP/HTTPS traffic
            subprocess.run([
                "iptables", "-t", "nat", "-A", "PREROUTING", "-i", self.client_interface,
                "-p", "tcp", "--dport", 80, "-j", "AUTH_REDIRECT"
            ], check=True)

            subprocess.run([
                "iptables", "-t", "nat", "-A", "PREROUTING", "-i", self.client_interface,
                "-p", "tcp", "--dport", 443, "-j", "AUTH_REDIRECT"
            ], check=True)

            # Redirect DNS queries
            subprocess.run([
                "iptables", "-t", "nat", "-A", "PREROUTING", "-i", self.client_interface,
                "-p", "udp", "--dport", 53, "-j", "REDIRECT", "--to-port", 53
            ], check=True)

            # Setup AUTH_REDIRECT chain
            subprocess.run([
                "iptables", "-t", "nat", "-A", "AUTH_REDIRECT", "-p", "tcp",
                "--dport", 80, "-j", "REDIRECT", "--to-port", self.captive_port
            ], check=True)

            subprocess.run([
                "iptables", "-t", "nat", "-A", "AUTH_REDIRECT", "-p", "tcp",
                "--dport", 443, "-j", "REDIRECT", "--to-port", self.captive_port
            ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error adding NAT rules: {e}")
            return False

    def add_portal_chain_rules(self) -> bool:
        """Add captive portal chain rules"""
        print("Setting captive portal chain rules")
        try:
            # Main forwarding chain
            subprocess.run([
                "iptables", "-A", "FORWARD", "-i", self.client_interface,
                "-o", self.client_interface, "-j", "CAPTIVE_PORTAL"
            ], check=True)

            # Allow traffic to gateway
            subprocess.run([
                "iptables", "-A", "CAPTIVE_PORTAL", "-d", self.gateway_address,
                "-j", "ACCEPT"
            ], check=True)

            # Allow essential services
            subprocess.run([
                "iptables", "-A", "CAPTIVE_PORTAL", "-p", "udp", "--dport", 53,
                "-j", "ACCEPT"
            ], check=True)

            subprocess.run([
                "iptables", "-A", "CAPTIVE_PORTAL", "-p", "udp", "--dport", "67:68",
                "-j", "ACCEPT"
            ], check=True)

            # Allow HTTP/HTTPS traffic
            subprocess.run([
                "iptables", "-A", "CAPTIVE_PORTAL", "-p", "tcp", "--dport", 80,
                "-j", "ACCEPT"
            ], check=True)

            subprocess.run([
                "iptables", "-A", "CAPTIVE_PORTAL", "-p", "tcp", "--dport", 443,
                "-j", "ACCEPT"
            ], check=True)

            # Log new connections
            subprocess.run([
                "iptables", "-A", "CAPTIVE_PORTAL", "-m", "conntrack",
                "--ctstate", "NEW", "-j", "LOG", "--log-prefix", "CAPTIVE_NEW: "
            ], check=True)

            # Drop all other traffic
            subprocess.run(["iptables", "-A", "CAPTIVE_PORTAL", "-j", "DROP"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error adding portal chain rules: {e}")
            return False

    def add_nat_masquerade_rule(self) -> bool:
        """Add NAT masquerade rule"""
        print("Setting NAT masquerade")
        try:
            subprocess.run([
                "iptables", "-t", "nat", "-A", "POSTROUTING", "-o", self.internet_interface,
                "-j", "MASQUERADE"
            ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error adding NAT masquerade rule: {e}")
            return False

    def add_input_rules(self) -> bool:
        """Add input rules"""
        print("Setting input rules")
        try:
            # Allow loopback
            subprocess.run(["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"], check=True)

            # Allow established connections
            subprocess.run([
                "iptables", "-A", "INPUT", "-m", "state", "--state", "ESTABLISHED,RELATED",
                "-j", "ACCEPT"
            ], check=True)

            # Allow HTTP to captive portal
            subprocess.run([
                "iptables", "-A", "INPUT", "-p", "tcp", "--dport", self.captive_port,
                "-j", "ACCEPT"
            ], check=True)

            # Logging
            subprocess.run([
                "iptables", "-A", "INPUT", "-p", "tcp", "--dport", self.captive_port,
                "-j", "LOG", "--log-prefix", "CAPTIVE_PORTAL: "
            ], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error adding input rules: {e}")
            return False


# Initialize with shared config
captivesetup = CaptiveSetup()
