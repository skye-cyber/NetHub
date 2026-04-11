import subprocess
from typing import Optional
from .config import BaseConfig
from .error import ErrorHandler


error_handler = ErrorHandler("CaptiveSetup")


class CaptiveSetup:
    def __init__(self, config: Optional[BaseConfig] = BaseConfig()):
        self.config = config if config else BaseConfig()

        # Initialize attributes from config
        self.client_interface = self.config.CLIENT_INTERFACE
        self.internet_interface = self.config.INTERNET_INTERFACE
        self.BASE_DIR = self.config.BASE_DIR
        self.gateway_address = self.config.GATEWAY
        self.captive_port = self.config.CAPTIVE_PORT
        self.AUTH_DIR = self.config.AUTH_DIR
        self.mac_file = self.config.mac_file

        self.init_files()

    def setup(self) -> bool:
        """
        Setup captive portal configuration

        This matches expected standard based on tried out steps:
        1. Enable IP forwarding
        2. Clear all rules
        3. Create chains
        4. Set default policies (FORWARD = DROP)
        5. Add basic forwarding rules (established connections first)
        6. Add NAT redirect rules (HTTP/HTTPS → captive portal)
        7. Add captive portal chain rules (FORWARD → CAPTIVE_PORTAL chain)
        8. Add NAT masquerade
        9. Add input rules

        Note: FORWARD policy is DROP intentionally - all client traffic goes through
              CAPTIVE_PORTAL chain which allows only specific traffic.
        """
        try:
            print("=" * 60)
            print("Setting up Captive Portal (matching bash script)")
            print("=" * 60)

            self.enable_ip_forwarding()
            self.clear_rules()
            self.create_chains()
            self.add_default_rules()
            self.configure_basic_forwarding_rules()
            self.add_nat_rules()
            self.add_portal_chain_rules()
            self.add_nat_masquerade_rule()
            self.add_input_rules()

            print("\n" + "=" * 60)
            print("✅ Captive portal setup complete")
            print(f"   Gateway IP: {self.gateway_address}")
            print(f"   Captive port: {self.captive_port}")
            print(f"   HTTP/HTTPS → port {self.captive_port}")
            print("=" * 60)
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Error during setup: {e}")
            if hasattr(e, "stderr") and e.stderr:
                print(f"   Error details: {e.stderr}")
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
        """
        Set default iptables policies

        IMPORTANT: FORWARD policy is DROP (not ACCEPT)
        This is intentional - all client traffic must go through CAPTIVE_PORTAL chain
        """
        try:
            subprocess.run(["iptables", "-P", "INPUT", "ACCEPT"], check=True)
            subprocess.run(
                ["iptables", "-P", "FORWARD", "DROP"], check=True
            )  # DROP, not ACCEPT
            subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=True)
            print("✓ Default policies set (FORWARD = DROP)")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error setting default rules: {e}")
            return False

    def enable_ip_forwarding(self) -> bool:
        """Enable IP forwarding"""
        try:
            with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
                f.write("1")
            print("✓ IP forwarding enabled")
            return True
        except IOError as e:
            print(f"Error enabling IP forwarding: {e}")
            return False

    def create_chains(self) -> bool:
        """Create necessary iptables chains"""
        print("Creating chains")
        try:
            # Create CAPTIVE_PORTAL chain if it doesn't exist
            # If it exists, flush it (matches bash: 2>/dev/null || iptables -F CAPTIVE_PORTAL)
            subprocess.run(["iptables", "-N", "CAPTIVE_PORTAL"], check=False)
            subprocess.run(["iptables", "-F", "CAPTIVE_PORTAL"], check=True)

            # Create AUTH_REDIRECT chain if it doesn't exist
            # If it exists, flush it
            subprocess.run(
                ["iptables", "-t", "nat", "-N", "AUTH_REDIRECT"], check=False
            )
            subprocess.run(["iptables", "-t", "nat", "-F", "AUTH_REDIRECT"], check=True)

            print("✓ Chains created/cleared")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating chains: {e}")
            return False

    def configure_basic_forwarding_rules(self) -> bool:
        """
        Configure basic forwarding rules

        IMPORTANT: Order matters! Established connections rule must come first.
        This matches bash script exactly.
        """
        print("Setting basic forwarding rules")
        try:
            # 1. Allow established connections (MUST COME FIRST)
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "FORWARD",
                    "-i",
                    self.internet_interface,
                    "-o",
                    self.client_interface,
                    "-m",
                    "state",
                    "--state",
                    "ESTABLISHED,RELATED",
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # 2. Allow access to gateway (captive portal)
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "FORWARD",
                    "-i",
                    self.client_interface,
                    "-d",
                    self.gateway_address,
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # 3. Allow DNS queries
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "FORWARD",
                    "-i",
                    self.client_interface,
                    "-o",
                    self.internet_interface,
                    "-p",
                    "udp",
                    "--dport",
                    "53",
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            print("✓ Basic forwarding rules configured")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error configuring basic forwarding rules: {e}")
            return False

    def add_nat_rules(self) -> bool:
        """
        Add NAT redirect rules

        Redirects HTTP/HTTPS to captive portal, DNS to ourselves.
        """
        print("Setting NAT redirect rules")
        try:
            # Clear NAT rules (matching bash)
            subprocess.run(["iptables", "-t", "nat", "-F", "PREROUTING"], check=True)

            # Send HTTP traffic to AUTH_REDIRECT chain
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-A",
                    "PREROUTING",
                    "-i",
                    self.client_interface,
                    "-p",
                    "tcp",
                    "--dport",
                    "80",
                    "-j",
                    "AUTH_REDIRECT",
                ],
                check=True,
            )

            # Send HTTPS traffic to AUTH_REDIRECT chain
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-A",
                    "PREROUTING",
                    "-i",
                    self.client_interface,
                    "-p",
                    "tcp",
                    "--dport",
                    "443",
                    "-j",
                    "AUTH_REDIRECT",
                ],
                check=True,
            )

            # Redirect DNS queries to ourselves
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-A",
                    "PREROUTING",
                    "-i",
                    self.client_interface,
                    "-p",
                    "udp",
                    "--dport",
                    "53",
                    "-j",
                    "REDIRECT",
                    "--to-port",
                    "53",
                ],
                check=True,
            )

            # Setup AUTH_REDIRECT chain:
            # Redirect HTTP to captive portal
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-A",
                    "AUTH_REDIRECT",
                    "-p",
                    "tcp",
                    "--dport",
                    "80",
                    "-j",
                    "REDIRECT",
                    "--to-port",
                    self.captive_port,
                ],
                check=True,
            )

            # Redirect HTTPS to captive portal
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-A",
                    "AUTH_REDIRECT",
                    "-p",
                    "tcp",
                    "--dport",
                    "443",
                    "-j",
                    "REDIRECT",
                    "--to-port",
                    self.captive_port,
                ],
                check=True,
            )

            print("✓ NAT redirect rules configured")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error adding NAT rules: {e}")
            return False

    def add_portal_chain_rules(self) -> bool:
        """
        Add captive portal chain rules

        This is the CORE of the captive portal:
        1. Send all client→internet traffic to CAPTIVE_PORTAL chain
        2. CAPTIVE_PORTAL chain allows only specific traffic
        3. Everything else is dropped
        """
        print("Setting captive portal chain rules")
        try:
            # Main forwarding chain - send all client traffic to captive portal chain
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "FORWARD",
                    "-i",
                    self.client_interface,
                    "-o",
                    self.internet_interface,
                    "-j",
                    "CAPTIVE_PORTAL",
                ],
                check=True,
            )

            # Note: First position is reserved for authenticated MACs
            # (inserted later by update_firewall logic)
            # This is intentionally left empty

            # Allow traffic to gateway (CRITICAL - allows redirected traffic to reach portal)
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "CAPTIVE_PORTAL",
                    "-d",
                    self.gateway_address,
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # Allow essential services
            # DNS
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "CAPTIVE_PORTAL",
                    "-p",
                    "udp",
                    "--dport",
                    "53",
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # DHCP
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "CAPTIVE_PORTAL",
                    "-p",
                    "udp",
                    "--dport",
                    "67:68",
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # Allow HTTP/HTTPS traffic (it will be redirected by NAT rules)
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "CAPTIVE_PORTAL",
                    "-p",
                    "tcp",
                    "--dport",
                    "80",
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "CAPTIVE_PORTAL",
                    "-p",
                    "tcp",
                    "--dport",
                    "443",
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # Log new connections (optional)
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "CAPTIVE_PORTAL",
                    "-m",
                    "conntrack",
                    "--ctstate",
                    "NEW",
                    "-j",
                    "LOG",
                    "--log-prefix",
                    "CAPTIVE_NEW: ",
                ],
                check=True,
            )

            # Drop all other traffic from unauthenticated devices
            subprocess.run(
                ["iptables", "-A", "CAPTIVE_PORTAL", "-j", "DROP"], check=True
            )

            # # Add to CAPTIVE_PORTAL chain (unauthenticated clients only)
            # # Block DoH to known providers (Cloudflare, Google, etc.)
            # sudo iptables -I CAPTIVE_PORTAL 7 -p tcp --dport 443 -d 1.1.1.1 -j DROP
            # sudo iptables -I CAPTIVE_PORTAL 7 -p tcp --dport 443 -d 1.0.0.1 -j DROP
            # sudo iptables -I CAPTIVE_PORTAL 7 -p tcp --dport 443 -d 8.8.8.8 -j DROP
            # sudo iptables -I CAPTIVE_PORTAL 7 -p tcp --dport 443 -d 8.8.4.4 -j DROP
            # sudo iptables -I CAPTIVE_PORTAL 7 -p tcp --dport 853 -j DROP  # DNS-over-TLS
            print("✓ Captive portal chain rules configured")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error adding portal chain rules: {e}")
            return False

    def add_nat_masquerade_rule(self) -> bool:
        """Add NAT masquerade rule for internet access"""
        print("Setting NAT masquerade")
        try:
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-A",
                    "POSTROUTING",
                    "-o",
                    self.internet_interface,
                    "-j",
                    "MASQUERADE",
                ],
                check=True,
            )
            print("✓ NAT masquerade configured")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error adding NAT masquerade rule: {e}")
            return False

    def add_input_rules(self) -> bool:
        """Add input rules for the captive portal server"""
        print("Setting input rules")
        try:
            # Allow loopback
            subprocess.run(
                ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"], check=True
            )

            # Allow established connections
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "INPUT",
                    "-m",
                    "state",
                    "--state",
                    "ESTABLISHED,RELATED",
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # Allow HTTP to captive portal
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "INPUT",
                    "-p",
                    "tcp",
                    "--dport",
                    str(self.captive_port),
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )

            # Logging (optional)
            subprocess.run(
                [
                    "iptables",
                    "-A",
                    "INPUT",
                    "-p",
                    "tcp",
                    "--dport",
                    str(self.captive_port),
                    "-j",
                    "LOG",
                    "--log-prefix",
                    "CAPTIVE_PORTAL: ",
                ],
                check=True,
            )

            print("✓ Input rules configured")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error adding input rules: {e}")
            return False

    def verify_setup(self) -> bool:
        """
        Verify the setup matches expected standard

        Returns True if all checks pass
        """
        print("\n" + "=" * 60)
        print("Verifying Setup")
        print("=" * 60)

        checks = []

        # Check 1: FORWARD policy is DROP
        try:
            result = subprocess.run(
                ["iptables", "-L", "FORWARD", "-n"],
                capture_output=True,
                text=True,
                check=True,
            )
            is_drop = "policy DROP" in result.stdout
            checks.append(("FORWARD policy = DROP", is_drop, "Should be DROP"))
        except Exception:
            checks.append(("FORWARD policy check", False, "Failed"))

        # Check 2: Critical FORWARD rule exists
        try:
            result = subprocess.run(
                ["iptables", "-L", "FORWARD", "-n", "--line-numbers"],
                capture_output=True,
                text=True,
                check=True,
            )
            has_critical_rule = "-j CAPTIVE_PORTAL" in result.stdout
            checks.append(
                ("FORWARD → CAPTIVE_PORTAL rule", has_critical_rule, "Must exist")
            )
        except Exception:
            checks.append(("FORWARD rule check", False, "Failed"))

        # Check 3: HTTP redirect exists
        try:
            result = subprocess.run(
                ["iptables", "-t", "nat", "-L", "PREROUTING", "-n"],
                capture_output=True,
                text=True,
                check=True,
            )
            has_http_redirect = (
                "dpt:80" in result.stdout and "AUTH_REDIRECT" in result.stdout
            )
            checks.append(
                ("HTTP redirect rule", has_http_redirect, "Port 80 → AUTH_REDIRECT")
            )
        except Exception:
            checks.append(("HTTP redirect check", False, "Failed"))

        # Check 4: CAPTIVE_PORTAL chain exists
        try:
            result = subprocess.run(
                ["iptables", "-L", "CAPTIVE_PORTAL", "-n"],
                capture_output=True,
                text=True,
                check=False,
            )
            chain_exists = result.returncode == 0
            checks.append(("CAPTIVE_PORTAL chain", chain_exists, "Chain must exist"))
        except Exception:
            checks.append(("Chain check", False, "Failed"))

        # Print results
        all_passed = True
        for check_name, passed, details in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}: {details}")
            if not passed:
                all_passed = False

        print(
            f"\nResult: {'✅ All checks passed' if all_passed else '❌ Some checks failed'}"
        )
        return all_passed

    def cleanup(self) -> bool:
        """
        Cleanup iptables rules (for testing/debugging)

        Note: This removes ALL iptables rules, not just captive portal ones.
        Use with caution.
        """
        print("Cleaning up iptables rules...")
        try:
            subprocess.run(["iptables", "-F"], check=True)
            subprocess.run(["iptables", "-t", "nat", "-F"], check=True)
            subprocess.run(["iptables", "-X"], check=True)
            subprocess.run(["iptables", "-t", "nat", "-X"], check=True)

            # Reset policies to defaults
            subprocess.run(["iptables", "-P", "INPUT", "ACCEPT"], check=True)
            subprocess.run(["iptables", "-P", "FORWARD", "ACCEPT"], check=True)
            subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=True)

            print("✅ Cleanup complete")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Cleanup failed: {e}")
            return False


# Initialize with shared config
captivesetup = CaptiveSetup()
