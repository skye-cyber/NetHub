#!/usr/bin/env python3
"""
Test script to verify signal and mutex fixes
"""
import os
import sys
import tempfile
import shutil

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from hotspotmanager.cleanup import CleanupManager
from hotspotmanager.lock import LockManager
from hotspotmanager.signals import SignalHandler

def test_signal_handler():
    """Test that SignalHandler works without AttributeError"""
    print("Testing SignalHandler...")
    
    try:
        # Test SignalHandler initialization
        config = {'test': 'config'}
        signal_handler = SignalHandler(config)
        
        # Check that original signal handlers are set
        assert hasattr(signal_handler, 'original_sigint_handler'), "Missing original_sigint_handler"
        assert hasattr(signal_handler, 'original_sigusr1_handler'), "Missing original_sigusr1_handler"
        assert hasattr(signal_handler, 'original_sigusr2_handler'), "Missing original_sigusr2_handler"
        
        print("✅ SignalHandler test passed")
        return True
    except Exception as e:
        print(f"❌ SignalHandler test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_cleanup_manager():
    """Test that CleanupManager works without AttributeError"""
    print("Testing CleanupManager...")
    
    try:
        # Create a mock ap_man object
        class MockApMan:
            def __init__(self):
                self.config = {
                    'conf_dir': '/tmp/test_conf',
                    'proc_dir': '/tmp/test_proc',
                    'internet_iface': 'eth0',
                    'wifi_iface': 'wlan0',
                    'gateway': '192.168.1.1',
                    'share_method': 'nat',
                    'no_virt': True
                }
                self.lock = LockManager()
                self.netmanager = None
        
        mock_ap_man = MockApMan()
        
        # Test CleanupManager initialization
        cleanup_manager = CleanupManager(mock_ap_man)
        
        # Check that it inherits signal handlers properly
        assert hasattr(cleanup_manager, 'original_sigint_handler'), "CleanupManager missing original_sigint_handler"
        assert hasattr(cleanup_manager, 'original_sigusr1_handler'), "CleanupManager missing original_sigusr1_handler"
        assert hasattr(cleanup_manager, 'original_sigusr2_handler'), "CleanupManager missing original_sigusr2_handler"
        
        print("✅ CleanupManager test passed")
        return True
    except Exception as e:
        print(f"❌ CleanupManager test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_mutex_locking():
    """Test that mutex locking works without 'Failed to lock mutex counter'"""
    print("Testing mutex locking...")
    
    try:
        # Create a lock manager
        lock_manager = LockManager()
        
        # Test mutex lock
        lock_success = lock_manager.mutex_lock()
        if not lock_success:
            print("❌ Mutex lock failed")
            return False
        
        # Test mutex unlock
        unlock_success = lock_manager.mutex_unlock()
        if not unlock_success:
            print("❌ Mutex unlock failed")
            return False
        
        print("✅ Mutex locking test passed")
        return True
    except Exception as e:
        print(f"❌ Mutex locking test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_cleanup_functionality():
    """Test that cleanup functionality works"""
    print("Testing cleanup functionality...")
    
    try:
        # Create a mock ap_man object
        class MockApMan:
            def __init__(self):
                # Create temporary directories for testing in current directory
                self.test_dir = os.path.join(os.getcwd(), 'test_hotspot_cleanup')
                self.conf_dir = os.path.join(self.test_dir, 'conf')
                self.proc_dir = os.path.join(self.test_dir, 'proc')
                
                # Clean up any existing test directories
                if os.path.exists(self.test_dir):
                    shutil.rmtree(self.test_dir, ignore_errors=True)
                
                os.makedirs(self.conf_dir, exist_ok=True)
                os.makedirs(self.proc_dir, exist_ok=True)
                
                self.config = {
                    'conf_dir': self.conf_dir,
                    'proc_dir': self.proc_dir,
                    'internet_iface': 'eth0',
                    'wifi_iface': 'wlan0',
                    'gateway': '192.168.1.1',
                    'share_method': 'nat',
                    'no_virt': True,
                    'running_as_daemon': False
                }
                self.lock = LockManager()
                self.netmanager = None
        
        mock_ap_man = MockApMan()
        
        # Test CleanupManager initialization
        cleanup_manager = CleanupManager(mock_ap_man)
        
        # Test basic cleanup
        cleanup_manager._basic_cleanup()
        
        # Cleanup test directories
        shutil.rmtree(mock_ap_man.test_dir, ignore_errors=True)
        
        print("✅ Cleanup functionality test passed")
        return True
    except Exception as e:
        print(f"❌ Cleanup functionality test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=== Signal and Mutex Fixes Test Suite ===")
    
    tests = [
        test_signal_handler,
        test_cleanup_manager,
        test_mutex_locking,
        test_cleanup_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"=== Test Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All tests passed! The fixes are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)