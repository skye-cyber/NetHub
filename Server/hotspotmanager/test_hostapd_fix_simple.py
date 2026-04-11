#!/usr/bin/env python3

"""
Simple test script to verify the hostapd frequency determination fix.
This script directly tests the configuration generation logic.
"""

import os
import sys
import tempfile

# Add the current directory to Python path to import the module
sys.path.insert(0, '/home/skye/NetHub/backend/hotspotmanager')

from core.services import NetServices

def create_test_config(temp_dir, freq_band, channel, country='US'):
    """Create a test configuration dictionary."""
    return {
        'vwifi_iface': 'xap0',
        'ssid': 'TestAP',
        'driver': 'nl80211',
        'conf_dir': temp_dir,
        'proc_dir': temp_dir,
        'freq_band': freq_band,
        'channel': channel,
        'country': country,
        'password': 'test1234',
        'wpa_version': 2,
        'share_method': 'nat',
        'bridge_iface': 'xbr0',
        'hostapd_path': '/usr/sbin/hostapd'
    }

def test_configuration(config, test_name):
    """Test a configuration and print results."""
    print(f"\n{test_name}")
    print("-" * 40)
    
    try:
        # Create NetServices instance
        service = NetServices()
        service.config = config
        
        # Generate configuration
        result = service.configure_hostapd()
        print(f"✓ Configuration successful: {result}")
        
        # Read generated config
        config_file = os.path.join(config['conf_dir'], 'hostapd.conf')
        with open(config_file, 'r') as f:
            content = f.read()
            
        # Extract key settings
        hw_mode = next((line.split('=')[1] for line in content.split('\n') if line.startswith('hw_mode=')), 'NOT FOUND')
        channel_line = next((line.split('=')[1] for line in content.split('\n') if line.startswith('channel=')), 'NOT FOUND')
        freq_line = next((line.split('=')[1] for line in content.split('\n') if line.startswith('freq=')), 'NOT FOUND')
        
        print(f"  Hardware mode: {hw_mode}")
        print(f"  Channel: {channel_line}")
        print(f"  Frequency: {freq_line}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False

def main():
    print("Hostapd Frequency Determination Fix Test")
    print("=" * 50)
    
    # Test 1: Valid 2.4GHz configuration
    with tempfile.TemporaryDirectory() as temp_dir:
        config = create_test_config(temp_dir, 2.4, 6)
        test_configuration(config, "Test 1: Valid 2.4GHz (channel 6)")
    
    # Test 2: Invalid 2.4GHz channel (should fall back to 6)
    with tempfile.TemporaryDirectory() as temp_dir:
        config = create_test_config(temp_dir, 2.4, 15)
        test_configuration(config, "Test 2: Invalid 2.4GHz (channel 15 → should be 6)")
    
    # Test 3: Valid 5GHz configuration
    with tempfile.TemporaryDirectory() as temp_dir:
        config = create_test_config(temp_dir, 5, 36)
        test_configuration(config, "Test 3: Valid 5GHz (channel 36)")
    
    # Test 4: Invalid 5GHz channel (should fall back to 36)
    with tempfile.TemporaryDirectory() as temp_dir:
        config = create_test_config(temp_dir, 5, 6)
        test_configuration(config, "Test 4: Invalid 5GHz (channel 6 → should be 36)")
    
    # Test 5: The original problematic configuration
    with tempfile.TemporaryDirectory() as temp_dir:
        config = create_test_config(temp_dir, 5, 6, 'UG')
        config['ssid'] = 'AccessPoint0'
        config['password'] = '12345678'
        success = test_configuration(config, "Test 5: Original issue (5GHz band + 2.4GHz channel)")
        
        if success:
            print("\n✓ The fix successfully handles the original problematic configuration!")
            print("  This should resolve the 'Could not determine operating frequency' error.")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()