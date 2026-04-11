import subprocess


class StopCaptive:
    def __init__(self):
        ...

    def stop(self) -> bool:
        """
        Stop captive portal
        """
        # Stop device detection

        self.stop_services()
        self.clear_iptables()
        print("Captive portal stopped")
        return True

    def stop_services(self):
        # Stop dnsmaq
        subprocess.run(['service', 'dnsmasq', 'stop'], check=True)

    def clear_iptables(self):
        subprocess.run(["iptables", "-F"], check=True)
        subprocess.run(["iptables", "-t", "nat", "-F"], check=True)
        subprocess.run(["iptables", "-X"], check=True)
        subprocess.run(["iptables", "-t", "nat", "-X"], check=True)


stopcaptive = StopCaptive()
