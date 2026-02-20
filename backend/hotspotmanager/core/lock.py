import os
import fcntl
import subprocess


class LockManager:
    def __init__(self):
        self.LOCK_FILE = "/tmp/ap_manager.all.lock"
        self.COUNTER_LOCK_FILE = f"/tmp/ap_manager.{os.getpid()}.lock"
        self.lock_fd = None
        self.counter_mutex_fd = None

        # Initialize the lock files
        self.__init_lock__()

    def __init_lock__(self):
        """Initialize the lock file with proper permissions"""
        try:
            # Set umask to allow all users to write to the lock file
            old_umask = os.umask(0o0555)

            # Clean up any existing lock
            self.cleanup_lock()

            # Open/create lock file with proper cleanup
            try:
                self.lock_fd = os.open(self.LOCK_FILE, os.O_RDWR | os.O_CREAT, 0o666)

                # Change ownership to root if we're not root
                if os.geteuid() != 0:
                    try:
                        os.chown(self.LOCK_FILE, 0, 0)
                    except OSError:
                        pass  # Ignore if we can't change ownership

                # Create mutex counter lock file
                with open(self.COUNTER_LOCK_FILE, 'w') as f:
                    f.write('0')
                os.chmod(self.COUNTER_LOCK_FILE, 0o666)

            except OSError as e:
                print(f"Failed to initialize lock file: {str(e)}")
                # Ensure we close any open file descriptors
                if hasattr(self, 'lock_fd') and self.lock_fd:
                    try:
                        os.close(self.lock_fd)
                    except OSError:
                        pass
                    self.lock_fd = None
                return False
            finally:
                # Restore original umask
                os.umask(old_umask)

            return True
        except Exception as e:
            print(f"Unexpected error in lock initialization: {str(e)}")
            return False

    def get_avail_fd(self):
        """Get an unused file descriptor"""
        try:
            # Use a simple approach - just return a high file descriptor number
            # This is more reliable than trying to find gaps in /proc
            return 100  # Start from a high number to avoid conflicts
        except Exception:
            return None  # Return None if any error occurs

    def cleanup_lock(self):
        """Clean up the lock files"""
        try:
            if os.path.exists(self.COUNTER_LOCK_FILE):
                os.remove(self.COUNTER_LOCK_FILE)
        except OSError:
            pass

    def mutex_lock(self):
        """Recursive mutex lock for all processes"""
        counter_fd = None
        try:
            # Ensure the counter lock file exists
            if not os.path.exists(self.COUNTER_LOCK_FILE):
                with open(self.COUNTER_LOCK_FILE, 'w') as f:
                    f.write('0')
                os.chmod(self.COUNTER_LOCK_FILE, 0o666)

            # Open the counter lock file
            counter_fd = os.open(self.COUNTER_LOCK_FILE, os.O_RDWR)

            # Lock the file
            fcntl.flock(counter_fd, fcntl.LOCK_EX)

            # Read the current counter value
            os.lseek(counter_fd, 0, os.SEEK_SET)
            counter_data = os.read(counter_fd, 1024).decode().strip()
            counter = int(counter_data) if counter_data else 0

            # Initialize lock_fd if not already done
            if not hasattr(self, 'lock_fd') or self.lock_fd is None:
                self.__init_lock__()

            # Lock the global mutex if this is the first lock
            if counter == 0 and hasattr(self, 'lock_fd') and self.lock_fd:
                try:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_EX)
                except OSError as e:
                    print(f"Failed to lock global mutex: {str(e)}")
                    # Close counter file before returning
                    if counter_fd:
                        try:
                            fcntl.flock(counter_fd, fcntl.LOCK_UN)
                            os.close(counter_fd)
                        except OSError:
                            pass
                    return False

            # Increment the counter
            counter += 1

            # Write the new counter value
            os.lseek(counter_fd, 0, os.SEEK_SET)
            os.ftruncate(counter_fd, 0)
            os.write(counter_fd, str(counter).encode())

            # Unlock the counter file
            fcntl.flock(counter_fd, fcntl.LOCK_UN)
            os.close(counter_fd)
            counter_fd = None

            return True
        except (OSError, ValueError, AttributeError) as e:
            print(f"Failed to lock mutex counter: {str(e)}")
            # Ensure we clean up the counter file descriptor
            if counter_fd:
                try:
                    if hasattr(counter_fd, 'fileno'):
                        os.close(counter_fd.fileno())
                    else:
                        os.close(counter_fd)
                except OSError:
                    pass
            return False

    def mutex_unlock(self):
        """Recursive mutex unlock for all processes"""
        counter_fd = None
        try:
            # Ensure the counter lock file exists
            if not os.path.exists(self.COUNTER_LOCK_FILE):
                return True  # Nothing to unlock

            # Open the counter lock file
            counter_fd = os.open(self.COUNTER_LOCK_FILE, os.O_RDWR)

            # Lock the file
            fcntl.flock(counter_fd, fcntl.LOCK_EX)

            # Read the current counter value
            os.lseek(counter_fd, 0, os.SEEK_SET)
            counter_data = os.read(counter_fd, 1024).decode().strip()
            counter = int(counter_data) if counter_data else 0

            # Decrement the counter if it's positive
            if counter > 0:
                counter -= 1

                # Unlock the global mutex if this is the last unlock
                if counter == 0 and hasattr(self, 'lock_fd') and self.lock_fd:
                    try:
                        fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                    except OSError as e:
                        print(f"Failed to unlock global mutex: {str(e)}")

            # Write the new counter value
            os.lseek(counter_fd, 0, os.SEEK_SET)
            os.ftruncate(counter_fd, 0)
            os.write(counter_fd, str(counter).encode())

            # Unlock the counter file
            fcntl.flock(counter_fd, fcntl.LOCK_UN)
            os.close(counter_fd)
            counter_fd = None

            return True
        except (OSError, ValueError, AttributeError) as e:
            print(f"Failed to unlock mutex counter: {str(e)}")
            # Ensure we clean up the counter file descriptor
            if counter_fd:
                try:
                    if hasattr(counter_fd, 'fileno'):
                        os.close(counter_fd.fileno())
                    else:
                        os.close(counter_fd)
                except OSError:
                    pass
            return False


lock = LockManager()
