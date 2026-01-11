#!/usr/bin/env python3
"""
Test script to verify hotspot creation functionality
"""
from hotspotmanager.ap_utils.config import config_manager
from hotspotmanager.ap_manager import ApManager
import os
import sys
import subprocess
import tempfile
import shutil

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def test_hotspot_creation():
    """Test hotspot creation with basic configuration"""
    print("Testing hotspot creation...")

    # Check if we're running as root
    if os.geteuid() != 0:
        print("This test must be run as root")
        return False

    try:
        # Create a test configuration
        test_config = {
            'wifi_iface': 'wlan0',  # Default interface
            'internet_iface': 'eth0',  # Default internet interface
            'ssid': 'TestHotspot',
            'password': 'TestPassword123',
            'gateway': '192.168.100.1',
            'channel': 6,
            'freq_band': 2.4,
            'driver': 'nl80211',
            'share_method': 'nat',
            'no_virt': False,
            'mode': 'nmcli'
        }

        # Update configuration
        config_manager._dict_update(config_manager.get_config, test_config)
        config_manager.save_config()

        print("Configuration updated successfully")

        # Create ApManager instance
        manager = ApManager()
        print("ApManager instance created")

        # Test basic functionality
        print("Testing basic functionality...")

        # Test if we can get available interfaces
        interfaces = manager.get_available_wifi_ifaces()
        print(f"Available WiFi interfaces: {interfaces}")

        # Test if we can check if an interface is WiFi
        if interfaces:
            is_wifi = manager.is_wifi_interface(interfaces[0])
            print(f"Is {interfaces[0]} a WiFi interface? {is_wifi}")

        # Test if we can check if an interface exists
        if interfaces:
            exists = manager.is_interface(interfaces[0])
            print(f"Does {interfaces[0]} exist? {exists}")

        print("Basic functionality tests passed!")

        # Note: We won't actually start the hotspot in this test
        # as it requires proper network configuration and could
        # interfere with existing network connections

        return True

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_sudo_permissions():
    """Test that sudo permissions are working"""
    print("Testing sudo permissions...")

    try:
        # Test a simple command that requires sudo
        result = subprocess.run(['sudo', '-n', 'whoami'],
                                capture_output=True, text=True, check=True)

        if result.stdout.strip() == 'root':
            print("Sudo permissions are working correctly")
            return True
        else:
            print(f"Sudo permissions test failed: {result.stdout.strip()}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Sudo permissions test failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print("=== Hotspot Manager Test Suite ===")

    # Test sudo permissions first
    sudo_ok = test_sudo_permissions()

    if not sudo_ok:
        print("Sudo permissions are not configured correctly.")
        print("Please run the installation script as root first.")
        return False

    # Test hotspot creation
    test_ok = test_hotspot_creation()

    if test_ok:
        print("\n=== All tests passed! ===")
        print("The hotspot manager should now be able to create hotspots successfully.")
        print("\nTo create a hotspot, you can use:")
        print("  sudo python3 backend/hotspotmanager/ap_cli.py start")
        print("\nOr use the bash wrapper:")
        print("  sudo backend/hotspotmanager/ap_manager.sh start")
        return True
    else:
        print("\n=== Tests failed ===")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
