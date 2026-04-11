#!/usr/bin/env python3

"""
Test script to verify the captive portal integration
"""

from core.config import BaseConfig
from core.captive_entry import Captive
import sys
import os
import json
import tempfile

# Add the core directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))


def test_config_integration():
    """Test BaseConfig integration"""
    print("Testing BaseConfig integration...")

    # Test default config
    config = BaseConfig()
    print(f"Default GATEWAY_ADDRESS: {config.GATEWAY_ADDRESS}")
    print(f"Default CLIENT_INTERFACE: {config.CLIENT_INTERFACE}")

    # Test config update with kwargs
    config.update_config(GATEWAY_ADDRESS="192.168.1.1", CLIENT_INTERFACE="wlan0")
    print(f"Updated GATEWAY_ADDRESS: {config.GATEWAY_ADDRESS}")
    print(f"Updated CLIENT_INTERFACE: {config.CLIENT_INTERFACE}")

    # Test JSON config
    json_config = {
        "GATEWAY_ADDRESS": "10.0.0.1",
        "CLIENT_INTERFACE": "eth1",
        "CAPTIVE_PORT": "9000"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(json_config, f)
        temp_json_file = f.name

    try:
        # Test loading from JSON
        config2 = BaseConfig(config_file=temp_json_file)
        print(f"JSON config GATEWAY_ADDRESS: {config2.GATEWAY_ADDRESS}")
        print(f"JSON config CLIENT_INTERFACE: {config2.CLIENT_INTERFACE}")
        print(f"JSON config CAPTIVE_PORT: {config2.CAPTIVE_PORT}")

        # Test saving to JSON
        temp_output_file = tempfile.mktemp(suffix='.json')
        config2.save_to_json(temp_output_file)
        print(f"Config saved to {temp_output_file}")

    finally:
        os.unlink(temp_json_file)
        if os.path.exists(temp_output_file):
            os.unlink(temp_output_file)

    print("✓ BaseConfig integration test passed")


def test_captive_integration():
    """Test Captive class integration"""
    print("\nTesting Captive class integration...")

    # Test default captive instance
    captive = Captive()
    print(f"Captive config GATEWAY_ADDRESS: {captive.config.GATEWAY_ADDRESS}")

    # Test captive with custom config
    custom_config = BaseConfig(CLIENT_INTERFACE="wlan0", CAPTIVE_PORT="9090")
    captive2 = Captive(config=custom_config)
    print(f"Custom captive CLIENT_INTERFACE: {captive2.config.CLIENT_INTERFACE}")
    print(f"Custom captive CAPTIVE_PORT: {captive2.config.CAPTIVE_PORT}")

    # Test captive with kwargs
    captive3 = Captive(GATEWAY_ADDRESS="172.16.0.1", SUBNET="172.16.0.0/16")
    print(f"Kwargs captive GATEWAY_ADDRESS: {captive3.config.GATEWAY_ADDRESS}")
    print(f"Kwargs captive SUBNET: {captive3.config.SUBNET}")

    # Test status method
    status = captive.status()
    print(f"Captive status: running={status['running']}")

    # Test properties
    props = captive.properties
    print(f"Captive properties config keys: {list(props['config'].keys())}")

    print("✓ Captive class integration test passed")


def test_config_methods():
    """Test config update methods"""
    print("\nTesting config update methods...")

    captive = Captive()

    # Test update_config with kwargs
    captive.update_config(GATEWAY_ADDRESS="192.168.50.1")
    print(f"Updated via kwargs: {captive.config.GATEWAY_ADDRESS}")

    # Test update_config with JSON file
    json_config = {
        "CLIENT_INTERFACE": "test0",
        "INTERNET_INTERFACE": "test1"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(json_config, f)
        temp_json_file = f.name

    try:
        captive.update_config(config_file=temp_json_file)
        print(f"Updated via JSON CLIENT_INTERFACE: {captive.config.CLIENT_INTERFACE}")
        print(f"Updated via JSON INTERNET_INTERFACE: {captive.config.INTERNET_INTERFACE}")

    finally:
        os.unlink(temp_json_file)

    # Test save_config
    temp_output_file = tempfile.mktemp(suffix='.json')
    captive.save_config(temp_output_file)
    print(f"Config saved successfully to {temp_output_file}")

    # Verify saved config
    with open(temp_output_file, 'r') as f:
        saved_config = json.load(f)
        print(f"Saved config has {len(saved_config)} keys")

    os.unlink(temp_output_file)
    print("✓ Config update methods test passed")


def main():
    """Main test function"""
    print("Starting captive portal integration tests...")

    try:
        test_config_integration()
        test_captive_integration()
        test_config_methods()

        print("\n🎉 All integration tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
