import subprocess
from typing import List
from pathlib import Path

from .setup import captivesetup
from .firewall import firewall


class StartCaptive:
    def __init__(self):
        self.interface = "xap0"
        self.log_file = Path('/etc/ap_manager/captive.log')
        self.dnsmasq_logfile = Path('/etc/ap_manager/dnsmasq.log')
        self.dnsmasq_config = Path("/etc/dnsmasq.d/ap_manager_portal.conf")
        self.gateway_address = '192.168.100.1'
        self.broadcast = f"{'.'.join(self.gateway_address.split('.')[:-1])}.255"
        self.dhcp_range = "192.168.100.10,192.168.100.100,255.255.255.0,12h"
        self.dnsmasq_leasefile = Path('/var/lib/misc/dnsmasq.leases')

    def start(self) -> bool:
        """Start the captive portal service"""
        print("Starting captive portal...")
        self.stop_services()
        self.configure_interface()
        self.configure_dnsmasq()
        captivesetup.setup()
        firewall.update([])
        self.test_config()
        return True

    def configure_dnsmasq(self) -> bool:
        """Configure dnsmasq service"""
        config = [
            # Listening interface
            f"interface={self.interface}",
            f"listen-address={self.gateway_address}",

            # DHCP range
            f"dhcp-range={self.dhcp_range}",

            # Gateway
            f"dhcp-option=3,{self.gateway_address}",

            # DNS options
            "dhcp-option=tag:authenticated,6,8.8.8.8,1.1.1.1",
            f"dhcp-option=tag:!authenticated,6,{self.gateway_address}",

            # DNS forwarders
            "server=8.8.8.8",
            "server=1.1.1.1",

            # Logging
            "log-dhcp",
            "log-queries",
            f"log-facility={self.dnsmasq_logfile}",
            f"dhcp-leasefile={self.dnsmasq_leasefile}",
            "dhcp-rapid-commit"
        ]

        with open(self.dnsmasq_config, 'w') as f:
            f.write('\n'.join(config))
        return True

    def stop_services(self) -> bool:
        """Stop dnsmasq and Apache services"""
        subprocess.run(['service', 'dnsmasq', 'stop'], check=True)
        subprocess.run(['sudo', 'systemctl', 'stop', 'apache2'], check=True)
        return True

    def start_services(self) -> bool:
        """Start dnsmasq service"""
        subprocess.run(['sudo', 'systemctl', 'start', 'dnsmasq'], check=True)
        return True

    def configure_interface(self) -> bool:
        """Configure network interface"""
        subprocess.run([
            'ifconfig',
            self.interface,
            self.gateway_address,
            'netmask',
            '255.255.255.0',
            'broadcast',
            self.broadcast,
            'up'
        ], check=True)
        return True

    def test_config(self) -> bool:
        """Test dnsmasq configuration"""
        subprocess.run([
            'sudo',
            'dnsmasq',
            '--test',
            '-C',
            str(self.dnsmasq_config)
        ], check=True)

        print("\t- Testing DNS redirect from gateway...")
        subprocess.run([
            'nslookup',
            'google.com',
            self.gateway_address
        ], check=True)
        return True


startcaptive = StartCaptive()
