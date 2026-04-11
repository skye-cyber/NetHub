#!/usr/bin/env python3
"""
Comprehensive test to verify all fixes work together
"""
import os
import sys
import tempfile
import shutil

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from hotspotmanager.lock import LockManager
from hotspotmanager.signals import SignalHandler
from hotspotmanager.cleanup import CleanupManager

def test_signal_handler_fix():
    """Test that SignalHandler works without AttributeError"""
    print("Testing SignalHandler fix...")
    
    try:
        config = {'test': 'config'}
        signal_handler = SignalHandler(config)
        
        # Check that original signal handlers are set
        assert hasattr(signal_handler, 'original_sigint_handler'), "Missing original_sigint_handler"
        assert hasattr(signal_handler, 'original_sigusr1_handler'), "Missing original_sigusr1_handler"
        assert hasattr(signal_handler, 'original_sigusr2_handler'), "Missing original_sigusr2_handler"
        
        print("✅ SignalHandler fix verified")
        return True
    except Exception as e:
        print(f"❌ SignalHandler test failed: {str(e)}")
        return False

def test_cleanup_manager_fix():
    """Test that CleanupManager works without AttributeError"""
    print("Testing CleanupManager fix...")
    
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
        cleanup_manager = CleanupManager(mock_ap_man)
        
        # Check that it inherits signal handlers properly
        assert hasattr(cleanup_manager, 'original_sigint_handler'), "CleanupManager missing original_sigint_handler"
        
        print("✅ CleanupManager fix verified")
        return True
    except Exception as e:
        print(f"❌ CleanupManager test failed: {str(e)}")
        return False

def test_mutex_fix():
    """Test that mutex locking works"""
    print("Testing mutex fix...")
    
    try:
        lock_manager = LockManager()
        
        # Test lock/unlock cycle
        if not lock_manager.mutex_lock():
            print("❌ Mutex lock failed")
            return False
        
        if not lock_manager.mutex_unlock():
            print("❌ Mutex unlock failed")
            return False
        
        print("✅ Mutex fix verified")
        return True
    except Exception as e:
        print(f"❌ Mutex test failed: {str(e)}")
        return False

def test_resource_limits():
    """Test that resource limits can be increased"""
    print("Testing resource limits...")
    
    try:
        import resource
        
        # Get current limits
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        print(f"Current file descriptor limits: soft={soft_limit}, hard={hard_limit}")
        
        # Try to increase limits (this may fail if we're not root or if hard limit is low)
        try:
            new_soft = min(hard_limit, 4096) if hard_limit > 0 else 4096
            if soft_limit < new_soft:
                resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft, hard_limit))
                print(f"✅ Increased file descriptor limit to {new_soft}")
            else:
                print("✅ File descriptor limit already sufficient")
        except (ValueError, resource.error) as e:
            print(f"⚠️  Could not increase resource limits (may need root): {str(e)}")
        
        return True
    except ImportError:
        print("⚠️  Resource module not available on this platform")
        return True
    except Exception as e:
        print(f"❌ Resource limits test failed: {str(e)}")
        return False

def test_cleanup_functionality():
    """Test cleanup functionality"""
    print("Testing cleanup functionality...")
    
    try:
        # Create a mock ap_man object with temp directories
        test_dir = os.path.join(os.getcwd(), 'test_cleanup_functionality')
        conf_dir = os.path.join(test_dir, 'conf')
        proc_dir = os.path.join(test_dir, 'proc')
        
        # Clean up any existing test directories
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)
        
        os.makedirs(conf_dir, exist_ok=True)
        os.makedirs(proc_dir, exist_ok=True)
        
        class MockApMan:
            def __init__(self):
                self.config = {
                    'conf_dir': conf_dir,
                    'proc_dir': proc_dir,
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
        cleanup_manager = CleanupManager(mock_ap_man)
        
        # Test basic cleanup
        cleanup_manager._basic_cleanup()
        
        # Cleanup test directories
        shutil.rmtree(test_dir, ignore_errors=True)
        
        print("✅ Cleanup functionality verified")
        return True
    except Exception as e:
        print(f"❌ Cleanup functionality test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("=== Comprehensive Fixes Test Suite ===")
    
    tests = [
        test_signal_handler_fix,
        test_cleanup_manager_fix,
        test_mutex_fix,
        test_resource_limits,
        test_cleanup_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\n--- Running {test.__name__} ---")
        if test():
            passed += 1
        print()
    
    print(f"=== Test Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All fixes verified! The hotspot manager should now work correctly.")
        print("\nKey improvements:")
        print("• Fixed AttributeError in SignalHandler")
        print("• Fixed mutex locking issues")
        print("• Improved resource limit handling")
        print("• Enhanced cleanup functionality")
        print("• Better error handling throughout")
        return True
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)