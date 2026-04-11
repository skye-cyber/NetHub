import subprocess
import re
from typing import List, Callable, Optional
from ap_utils.colors import fg
from .config import BaseConfig
from .error import ErrorHandler

error_handler = ErrorHandler("CaptiveStart")


class Firewall:
    def __init__(self, config: BaseConfig = BaseConfig()):
        self.config = config if config else BaseConfig()
        self.client_interface = self.config.CLIENT_INTERFACE
        self.internet_interface = self.config.INTERNET_INTERFACE
        self.BASE_DIR = self.config.BASE_DIR
        self.gateway_address = self.config.GATEWAY
        self.subnet = self.config.SUBNET
        self.captive_port = self.config.CAPTIVE_PORT
        self.AUTH_DIR = self.config.AUTH_DIR
        self.mac_file = self.config.mac_file

    def get_existing(self) -> int:
        """Get count of existing MAC rules in CAPTIVE_PORTAL chain"""
        try:
            result = subprocess.run(
                ["iptables", "-L", "CAPTIVE_PORTAL", "-n"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            existing_mac_count = len(
                [
                    line
                    for line in result.stdout.split("\n")
                    if re.search(
                        r"MAC\s+([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})",
                        line,
                        re.IGNORECASE,
                    )
                ]
            )
            print(
                f"Found {existing_mac_count} existing MAC rules in CAPTIVE_PORTAL chain"
            )
            return existing_mac_count
        except Exception:
            return 0

    def update(self, macs: List[str]) -> bool:
        """Update firewall rules for given MAC addresses"""
        self.process_macs(macs=macs, callback=self.flush_contrac)
        print("Firewall rules updated")
        return True

    @error_handler.exception_factory(Exception)
    def verify_chains(self):
        """Verify and display current iptables chains"""
        print("CAPTIVE_PORTAL chain:")
        with error_handler.context(lambda: ...):
            subprocess.run(
                ["iptables", "-L", "CAPTIVE_PORTAL", "-n", "--line-numbers"], check=True
            )

        print("\nAUTH_REDIRECT chain:")
        with error_handler.context(lambda: ...):
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-L",
                    "AUTH_REDIRECT",
                    "-n",
                    "--line-numbers",
                ],
                check=True,
            )

    @error_handler.exception_factory(Exception)
    def verify_chains_verbose(self):
        print(
            f"\n{fg.BYELLOW}1. {fg.RESET}{fg.FWHITE}Current NAT PREROUTING rules:{fg.RESET}\n"
        )
        subprocess.run(
            [
                "sudo",
                "iptables",
                "-t",
                "nat",
                "-L",
                "PREROUTING",
                "-n",
                "--line-numbers",
                "-v",
            ],
            check=True,
        )

        print(
            f"\n{fg.BYELLOW}2. {fg.RESET}{fg.FWHITE}Current FORWARD chain:{fg.RESET}\n"
        )
        subprocess.run(
            ["sudo", "iptables", "-L", "FORWARD", "-n", "--line-numbers", "-v"],
            check=True,
        )

        print(
            f"\n{fg.BYELLOW}3. {fg.RESET}{fg.FWHITE}Checking if packets are hitting the rules:{fg.RESET}\n"
        )
        print("\tClear counters first...")
        subprocess.run(["sudo", "iptables", "-t", "nat", "-Z"], check=True)
        subprocess.run(["sudo", "iptables", "-Z"], check=True)

        print("\n\t♉Now generate traffic from a connected device...")
        print("\tOr run this from another device: curl -v http://example.com")
        input("\t⇾ Press Enter after generating traffic...")

        print(f"\n{fg.BYELLOW}4. {fg.RESET}{fg.FWHITE}Packet counters:{fg.RESET}\n")
        print("\tNAT PREROUTING")
        subprocess.run(
            [
                "sudo",
                "iptables",
                "-t",
                "nat",
                "-L",
                "PREROUTING",
                "-n",
                "-v",
                "--line-numbers",
            ],
            check=True,
        )

        print("\n\tFORWARD chain:")
        subprocess.run(
            ["sudo", "iptables", "-L", "FORWARD", "-n", "-v", "--line-numbers"],
            check=True,
        )

        print(f"\n{fg.BYELLOW}5. {fg.RESET}{fg.FWHITE}Interface status:{fg.RESET}\n")
        subprocess.run(["ip", "addr", "show", self.client_interface], check=True)

        print("\tRouting table:")
        subprocess.run(["ip", "route", "show"], check=True)
        subprocess.run([], check=True)

    def process_macs(
        self,
        macs: Optional[List[str]],
        callback: Optional[Callable[[str], bool]] = None,
    ):
        """Process MAC addresses and apply callback if provided"""
        if not macs:
            return

        for mac in macs:
            mac = mac.strip()
            if not mac:
                continue

            cleaned_mac = self.clean_mac(mac)
            if not self.validate_mac(cleaned_mac):
                print(f"Invalid MAC format: {mac}")
                continue

            print(f"Processing MAC: {cleaned_mac}")
            if callback:
                callback(cleaned_mac)
            else:
                self.update_firewall_allow(cleaned_mac)

    def clean_mac_old(self, mac: str) -> str:
        """Clean and standardize MAC address format"""
        return re.sub(r"[^0-9a-fA-F]", "", mac).lower()

    def clean_mac(self, mac: str) -> str:
        """Clean and standardize MAC address format"""
        # Remove all non-hex characters
        cleaned = re.sub(r"[^0-9a-fA-F]", "", mac).lower()
        # Format as xx:xx:xx:xx:xx:xx
        if len(cleaned) == 12:
            return ":".join([cleaned[i : i + 2] for i in range(0, 12, 2)])
        return mac

    def validate_mac(self, mac: str) -> bool:
        """Validate MAC address format"""
        return bool(re.fullmatch(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$", mac, re.IGNORECASE))

    def update_firewall_allow_old(self, mac: str):
        """Update iptables rules for given MAC address to allow internet access"""
        # Check if MAC rule already exists in CAPTIVE_PORTAL
        if not self.rule_exists(mac):
            print(f"Adding internet access for MAC: {mac}")
            subprocess.run(
                [
                    "iptables",
                    "-I",
                    "CAPTIVE_PORTAL",
                    "1",
                    "-m",
                    "mac",
                    "--mac-source",
                    mac,
                    "-j",
                    "ACCEPT",
                ]
            )
        else:
            print(f"MAC {mac} already has access")

        # Check if MAC rule already exists in AUTH_REDIRECT
        check_cmd = [
            "iptables",
            "-t",
            "nat",
            "-C",
            "AUTH_REDIRECT",
            "-m",
            "mac",
            "--mac-source",
            mac,
        ]
        if (
            subprocess.run(
                check_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).returncode
            != 0
        ):
            print(f"Adding redirect exemption for MAC: {mac}")
            # Allow authenticated MAC to use real DNS (bypass local hijack)
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-I",
                    "AUTH_REDIRECT",
                    "1",
                    "-m",
                    "mac",
                    "--mac-source",
                    mac,
                    "-j",
                    "RETURN",  # Don't redirect to local, allow through
                ]
            )
        else:
            print(f"MAC {mac} already has redirect exemption")

    def _normalize_mac(self, mac: str) -> str:
        """Normalize MAC to lowercase with single-digit octets"""
        # Remove all separators
        clean = mac.replace(":", "").replace("-", "").replace(".", "").lower()
        # Validate length
        if len(clean) != 12 or not all(c in "0123456789abcdef" for c in clean):
            raise ValueError(f"Invalid MAC format: {mac}")
        # Format as xx:xx:xx:xx:xx:xx
        return ":".join(clean[i : i + 2] for i in range(0, 12, 2))

    def update_firewall_allow(self, mac: str):
        """
        Allow internet access for MAC address
        - Add ACCEPT rule in CAPTIVE_PORTAL chain
        - Add RETURN rule in AUTH_REDIRECT chain (bypass redirect)
        """
        mac = self._normalize_mac(mac)
        print(f"🔓 Allowing internet access for MAC: {mac}")

        # 1. Remove any existing DROP/block rules for this MAC
        self._remove_mac_rules(mac)

        # 2. Check if ACCEPT rule already exists in CAPTIVE_PORTAL
        if not self._mac_rule_exists("CAPTIVE_PORTAL", mac, "ACCEPT"):
            # Add ACCEPT rule at position after any existing authenticated rules
            print("  Adding ACCEPT rule to CAPTIVE_PORTAL chain")
            subprocess.run(
                [
                    "iptables",
                    "-A",  # Changed from -I to -A unless you need position 1 specifically
                    "CAPTIVE_PORTAL",
                    "-m",
                    "mac",
                    "--mac-source",
                    mac,
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )
        else:
            print("  ACCEPT rule already exists in CAPTIVE_PORTAL")

        # 3. Check if RETURN rule already exists in AUTH_REDIRECT
        if not self._mac_rule_exists("AUTH_REDIRECT", mac, "RETURN", table="nat"):
            print("  Adding RETURN rule to AUTH_REDIRECT chain")
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-A",  # Changed from -I unless position matters
                    "AUTH_REDIRECT",
                    "-m",
                    "mac",
                    "--mac-source",
                    mac,
                    "-j",
                    "RETURN",
                ],
                check=True,
            )
        else:
            print("  RETURN rule already exists in AUTH_REDIRECT")

        # 4. Flush connection tracking for immediate effect
        self.flush_contrac(mac)
        print(f"  ✓ Internet access enabled for {mac}")

    def _mac_rule_exists(
        self, chain: str, mac: str, target: str, table: str = "filter"
    ) -> bool:
        """Check if a MAC rule exists in a chain by parsing iptables output"""
        try:
            if table == "nat":
                cmd = ["iptables", "-t", "nat", "-L", chain, "-n"]
            else:
                cmd = ["iptables", "-L", chain, "-n"]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Look for pattern: target ... MAC xx:xx:xx:xx:xx:xx
            pattern = rf"{target}\s+.*MAC\s+{re.escape(mac)}"
            return bool(re.search(pattern, result.stdout, re.IGNORECASE))
        except subprocess.CalledProcessError:
            return False

    def update_firewall_block(self, mac: str):
        """
        Block internet access for MAC address
        - Remove ACCEPT/RETURN rules (reverts to default DROP/REDIRECT)
        """
        print(f"🔒 Blocking internet access for MAC: {mac}")

        # 1. Remove ACCEPT rule from CAPTIVE_PORTAL if exists
        self._remove_mac_accept_rule(mac)

        # 2. Remove RETURN rule from AUTH_REDIRECT if exists
        self._remove_mac_return_rule(mac)

        # 3. Flush connection tracking
        self.flush_contrac(mac)
        print(f"  ✓ Internet access blocked for {mac}")

    def _remove_mac_rules(self, mac: str):
        """Remove all iptables rules for a MAC address"""
        # Remove from CAPTIVE_PORTAL chain
        while True:
            result = subprocess.run(
                [
                    "iptables",
                    "-D",
                    "CAPTIVE_PORTAL",
                    "-m",
                    "mac",
                    "--mac-source",
                    mac,
                    "-j",
                    "ACCEPT",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                break

        # Remove from AUTH_REDIRECT chain
        while True:
            result = subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-D",
                    "AUTH_REDIRECT",
                    "-m",
                    "mac",
                    "--mac-source",
                    mac,
                    "-j",
                    "RETURN",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                break

    def _remove_mac_accept_rule(self, mac: str) -> bool:
        """Remove ACCEPT rule from CAPTIVE_PORTAL chain"""
        check_cmd = [
            "iptables",
            "-C",
            "CAPTIVE_PORTAL",
            "-m",
            "mac",
            "--mac-source",
            mac,
            "-j",
            "ACCEPT",
        ]

        if subprocess.run(check_cmd, capture_output=True).returncode == 0:
            print("  Removing ACCEPT rule from CAPTIVE_PORTAL")
            subprocess.run(
                [
                    "iptables",
                    "-D",
                    "CAPTIVE_PORTAL",
                    "-m",
                    "mac",
                    "--mac-source",
                    mac,
                    "-j",
                    "ACCEPT",
                ],
                check=True,
            )
            return True
        return False

    def _remove_mac_return_rule(self, mac: str) -> bool:
        """Remove RETURN rule from AUTH_REDIRECT chain"""
        check_cmd = [
            "iptables",
            "-t",
            "nat",
            "-C",
            "AUTH_REDIRECT",
            "-m",
            "mac",
            "--mac-source",
            mac,
            "-j",
            "RETURN",
        ]

        if subprocess.run(check_cmd, capture_output=True).returncode == 0:
            print("  Removing RETURN rule from AUTH_REDIRECT")
            subprocess.run(
                [
                    "iptables",
                    "-t",
                    "nat",
                    "-D",
                    "AUTH_REDIRECT",
                    "-m",
                    "mac",
                    "--mac-source",
                    mac,
                    "-j",
                    "RETURN",
                ],
                check=True,
            )
            return True
        return False

    def list_from_file(self, file: str) -> List[str]:
        """Read MAC addresses from file"""
        try:
            with open(file, "r") as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            return []

    def flush_contrac_old(self, mac: str) -> bool:
        """Flush connection tracking for given MAC address"""
        print(f"Flushing connection tracking for MAC: {mac}")
        return (
            subprocess.run(
                ["conntrack", "-D", "-m", mac],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )

    def flush_contrac(self, mac: str) -> bool:
        """Flush connection tracking for given MAC address"""
        print(f"  Flushing connection tracking for {mac}")
        result = subprocess.run(
            ["conntrack", "-D", "--orig-src", mac], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("    ✓ Connection tracking flushed")
            return True
        else:
            print("    ⚠ No connections to flush")
            return False

    def rule_exists(self, mac) -> bool:
        """Check if MAC rule already exists in CAPTIVE_PORTAL"""
        check_cmd = [
            "iptables",
            "-C",
            "CAPTIVE_PORTAL",
            "-m",
            "mac",
            "--mac-source",
            mac,
            "-j",
            "ACCEPT",
        ]
        return (
            subprocess.run(
                check_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ).returncode
            == 0
        )

    def get_authenticated_macs(self) -> List[str]:
        """Get list of authenticated MACs from iptables"""
        macs = []
        try:
            result = subprocess.run(
                ["iptables", "-L", "CAPTIVE_PORTAL", "-n", "--line-numbers"],
                capture_output=True,
                text=True,
                check=True,
            )

            for line in result.stdout.split("\n"):
                if "MAC" in line and "ACCEPT" in line:
                    # Extract MAC from line like:
                    # 1    ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0            MAC 00:11:22:33:44:55
                    match = re.search(r"MAC ([0-9a-f:]{17})", line)
                    if match:
                        macs.append(match.group(1).lower())

        except Exception as e:
            print(f"Error getting authenticated MACs: {e}")

        return macs

    def authenticate(self, mac: str):
        """Alias for update_firewall_allow"""
        return self.update_firewall_allow(mac)

    def deauthenticate(self, mac: str):
        """Alias for update_firewall_block"""
        return self.update_firewall_block(mac)

    def auth_status(self, mac: str):
        """Check if MAC is authenticated (has ACCEPT rule)"""
        return self.rule_exists(mac)


# Initialize firewall instance with shared config
firewall = Firewall()
