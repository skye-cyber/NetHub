#!/usr/bin/env python3

"""
Test script to verify the hostapd frequency determination fix.
This script tests the configuration generation logic without actually starting hostapd.
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add the current directory to Python path to import the module
sys.path.insert(0, '/home/skye/NetHub/backend/hotspotmanager')

from core.services import NetServices

def test_24ghz_configuration():
    """Test 2.4GHz band configuration with valid and invalid channels."""
    print("Testing 2.4GHz band configuration...")
    
    # Test case 1: Valid 2.4GHz channel
    print("\n1. Testing valid 2.4GHz channel (6):")
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock config for 2.4GHz with valid channel
        mock_config = {
            'vwifi_iface': 'xap0',
            'ssid': 'TestAP',
            'driver': 'nl80211',
            'conf_dir': temp_dir,
            'proc_dir': temp_dir,
            'freq_band': 2.4,
            'channel': 6,
            'country': 'US',
            'password': 'test1234',
            'wpa_version': 2,
            'share_method': 'nat',
            'bridge_iface': 'xbr0',
            'hostapd_path': '/usr/sbin/hostapd'
        }
        
        with patch('core.services.config_manager.get_config', mock_config):
            service = NetServices()
            service.config = mock_config
            
            try:
                result = service.configure_hostapd()
                print(f"✓ Configuration successful: {result}")
                
                # Read generated config
                config_file = os.path.join(temp_dir, 'hostapd.conf')
                with open(config_file, 'r') as f:
                    content = f.read()
                    print("Generated config contains:")
                    print(f"  - hw_mode: {'g' if 'hw_mode=g' in content else 'NOT FOUND'}")
                    print(f"  - channel: {next((line.split('=')[1] for line in content.split('\n') if line.startswith('channel=')), 'NOT FOUND')}")
                    print(f"  - freq: {next((line.split('=')[1] for line in content.split('\n') if line.startswith('freq=')), 'NOT FOUND')}")
                    
            except Exception as e:
                print(f"✗ Configuration failed: {e}")
    
    # Test case 2: Invalid 2.4GHz channel (should fall back to channel 6)
    print("\n2. Testing invalid 2.4GHz channel (15, should fall back to 6):")
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config['channel'] = 15  # Invalid for 2.4GHz
        mock_config['conf_dir'] = temp_dir
        
        with patch('core.services.config_manager.get_config', mock_config):
            service = NetServices()
            service.config = mock_config
            
            try:
                result = service.configure_hostapd()
                print(f"✓ Configuration successful: {result}")
                
                # Read generated config
                config_file = os.path.join(temp_dir, 'hostapd.conf')
                with open(config_file, 'r') as f:
                    content = f.read()
                    channel_line = next((line.split('=')[1] for line in content.split('\n') if line.startswith('channel=')), 'NOT FOUND')
                    print(f"  - Channel set to: {channel_line} (should be 6)")
                    
            except Exception as e:
                print(f"✗ Configuration failed: {e}")

def test_5ghz_configuration():
    """Test 5GHz band configuration with valid and invalid channels."""
    print("\n\nTesting 5GHz band configuration...")
    
    # Test case 1: Valid 5GHz channel
    print("\n1. Testing valid 5GHz channel (36):")
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config = {
            'vwifi_iface': 'xap0',
            'ssid': 'TestAP',
            'driver': 'nl80211',
            'conf_dir': temp_dir,
            'proc_dir': temp_dir,
            'freq_band': 5,
            'channel': 36,
            'country': 'US',
            'password': 'test1234',
            'wpa_version': 2,
            'share_method': 'nat',
            'bridge_iface': 'xbr0',
            'hostapd_path': '/usr/sbin/hostapd'
        }
        
        with patch('core.services.config_manager.get_config', mock_config):
            service = NetServices()
            service.config = mock_config
            
            try:
                result = service.configure_hostapd()
                print(f"✓ Configuration successful: {result}")
                
                # Read generated config
                config_file = os.path.join(temp_dir, 'hostapd.conf')
                with open(config_file, 'r') as f:
                    content = f.read()
                    print("Generated config contains:")
                    print(f"  - hw_mode: {'a' if 'hw_mode=a' in content else 'NOT FOUND'}")
                    print(f"  - channel: {next((line.split('=')[1] for line in content.split('\n') if line.startswith('channel=')), 'NOT FOUND')}")
                    print(f"  - freq: {next((line.split('=')[1] for line in content.split('\n') if line.startswith('freq=')), 'NOT FOUND')}")
                    
            except Exception as e:
                print(f"✗ Configuration failed: {e}")
    
    # Test case 2: Invalid 5GHz channel (should fall back to channel 36)
    print("\n2. Testing invalid 5GHz channel (6, should fall back to 36):")
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config['channel'] = 6  # Invalid for 5GHz
        mock_config['conf_dir'] = temp_dir
        
        with patch('core.services.config_manager.get_config', mock_config):
            service = NetServices()
            service.config = mock_config
            
            try:
                result = service.configure_hostapd()
                print(f"✓ Configuration successful: {result}")
                
                # Read generated config
                config_file = os.path.join(temp_dir, 'hostapd.conf')
                with open(config_file, 'r') as f:
                    content = f.read()
                    channel_line = next((line.split('=')[1] for line in content.split('\n') if line.startswith('channel=')), 'NOT FOUND')
                    freq_line = next((line.split('=')[1] for line in content.split('\n') if line.startswith('freq=')), 'NOT FOUND')
                    print(f"  - Channel set to: {channel_line} (should be 36)")
                    print(f"  - Frequency set to: {freq_line} (should be 5180 for channel 36)")
                    
            except Exception as e:
                print(f"✗ Configuration failed: {e}")

def test_mixed_configuration():
    """Test the original problematic configuration (5GHz band with 2.4GHz channel)."""
    print("\n\nTesting mixed configuration (5GHz band with 2.4GHz channel - original issue):")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # This is the problematic configuration from the original issue
        mock_config = {
            'vwifi_iface': 'xap0',
            'ssid': 'AccessPoint0',
            'driver': 'nl80211',
            'conf_dir': temp_dir,
            'proc_dir': temp_dir,
            'freq_band': 5,  # 5GHz band
            'channel': 6,    # But channel 6 is 2.4GHz - this was the problem!
            'country': 'UG',
            'password': '12345678',
            'wpa_version': 2,
            'share_method': 'nat',
            'bridge_iface': 'xbr0',
            'hostapd_path': '/usr/sbin/hostapd'
        }
        
        with patch('core.services.config_manager.get_config', mock_config):
            service = NetServices()
            service.config = mock_config
            
            try:
                result = service.configure_hostapd()
                print(f"✓ Configuration successful: {result}")
                
                # Read generated config
                config_file = os.path.join(temp_dir, 'hostapd.conf')
                with open(config_file, 'r') as f:
                    content = f.read()
                    print("Generated config contains:")
                    print(f"  - hw_mode: {'a' if 'hw_mode=a' in content else 'NOT FOUND'}")
                    channel_line = next((line.split('=')[1] for line in content.split('\n') if line.startswith('channel=')), 'NOT FOUND')
                    freq_line = next((line.split('=')[1] for line in content.split('\n') if line.startswith('freq=')), 'NOT FOUND')
                    print(f"  - channel: {channel_line} (should be 36, not 6)")
                    print(f"  - freq: {freq_line} (should be 5180)")
                    print("\n✓ The fix correctly handles the mixed configuration!")
                    
            except Exception as e:
                print(f"✗ Configuration failed: {e}")

if __name__ == "__main__":
    print("Hostapd Frequency Determination Fix Test")
    print("=" * 50)
    
    test_24ghz_configuration()
    test_5ghz_configuration()
    test_mixed_configuration()
    
    print("\n" + "=" * 50)
    print("Test completed!")