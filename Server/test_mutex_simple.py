#!/usr/bin/env python3
"""
Simple test to verify mutex locking works
"""
import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from hotspotmanager.lock import LockManager

def test_simple_mutex():
    """Test basic mutex functionality"""
    print("Testing simple mutex functionality...")
    
    try:
        # Create a lock manager
        lock_manager = LockManager()
        
        # Test mutex lock
        print("Testing mutex lock...")
        lock_success = lock_manager.mutex_lock()
        if not lock_success:
            print("❌ Mutex lock failed")
            return False
        print("✅ Mutex lock succeeded")
        
        # Test mutex unlock
        print("Testing mutex unlock...")
        unlock_success = lock_manager.mutex_unlock()
        if not unlock_success:
            print("❌ Mutex unlock failed")
            return False
        print("✅ Mutex unlock succeeded")
        
        # Test multiple lock/unlock cycles
        print("Testing multiple lock/unlock cycles...")
        for i in range(3):
            if not lock_manager.mutex_lock():
                print(f"❌ Mutex lock failed on cycle {i+1}")
                return False
            if not lock_manager.mutex_unlock():
                print(f"❌ Mutex unlock failed on cycle {i+1}")
                return False
        print("✅ Multiple lock/unlock cycles succeeded")
        
        print("✅ All mutex tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_simple_mutex()
    sys.exit(0 if success else 1)