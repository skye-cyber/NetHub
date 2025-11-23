import os
import fcntl
import subprocess


class LockManager:
    def __init__(self):
        self.LOCK_FILE = "/tmp/create_ap.all.lock"
        self.COUNTER_LOCK_FILE = f"/tmp/create_ap.{os.getpid()}.lock"
        self.lock_fd = None
        self.counter_mutex_fd = None

    def __init_lock__(self):
        """Initialize the lock file with proper permissions"""
        # Set umask to allow all users to write to the lock file
        old_umask = os.umask(0o0555)

        # Clean up any existing lock
        self.cleanup_lock()

        # Get an available file descriptor
        self.lock_fd = self.get_avail_fd()
        if self.lock_fd is None:
            return False

        # Open/create lock file
        try:
            # Open the file with write access
            self.lock_fd = os.open(self.LOCK_FILE, os.O_RDWR | os.O_CREAT, 0o666)

            # Change ownership to root if we're not root
            if os.geteuid() != 0:
                os.chown(self.LOCK_FILE, 0, 0)

            # Create mutex counter lock file
            with open(self.COUNTER_LOCK_FILE, 'w') as f:
                f.write('0')

            # Restore original umask
            os.umask(old_umask)
            return True
        except OSError:
            return False

    def get_avail_fd(self):
        """Get an unused file descriptor"""
        max_fds = os.sysconf('SC_OPEN_MAX')
        pid = os.getpid()

        for x in range(3, max_fds):  # Start from 3 to skip stdin, stdout, stderr
            if not os.path.exists(f"/proc/{pid}/fd/{x}"):
                return x

        return None  # Return None if no available FD found

    def cleanup_lock(self):
        """Clean up the lock files"""
        try:
            if os.path.exists(self.COUNTER_LOCK_FILE):
                os.remove(self.COUNTER_LOCK_FILE)
        except OSError:
            pass

    def mutex_lock(self):
        """Recursive mutex lock for all processes"""
        # Get a file descriptor for the counter lock
        self.counter_mutex_fd = self.get_avail_fd()
        if self.counter_mutex_fd is None:
            print("Failed to lock mutex counter")
            return False

        try:
            # Open the counter lock file
            counter_fd = os.open(self.COUNTER_LOCK_FILE, os.O_RDWR)

            # Lock the file
            fcntl.flock(counter_fd, fcntl.LOCK_EX)

            # Read the current counter value
            os.lseek(counter_fd, 0, os.SEEK_SET)
            counter = int(os.read(counter_fd, 1024).decode().strip())

            # Lock the global mutex if this is the first lock
            if counter == 0:
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX)

            # Increment the counter
            counter += 1

            # Write the new counter value
            os.lseek(counter_fd, 0, os.SEEK_SET)
            os.ftruncate(counter_fd, 0)
            os.write(counter_fd, str(counter).encode())

            # Unlock the counter file
            fcntl.flock(counter_fd, fcntl.LOCK_UN)
            os.close(counter_fd)

            return True
        except (OSError, ValueError):
            print("Failed to lock mutex counter")
            return False

    def mutex_unlock(self):
        """Recursive mutex unlock for all processes"""
        # Get a file descriptor for the counter lock
        self.counter_mutex_fd = self.get_avail_fd()
        if self.counter_mutex_fd is None:
            print("Failed to lock mutex counter")
            return False

        try:
            # Open the counter lock file
            counter_fd = os.open(self.COUNTER_LOCK_FILE, os.O_RDWR)

            # Lock the file
            fcntl.flock(counter_fd, fcntl.LOCK_EX)

            # Read the current counter value
            os.lseek(counter_fd, 0, os.SEEK_SET)
            counter = int(os.read(counter_fd, 1024).decode().strip())

            # Decrement the counter if it's positive
            if counter > 0:
                counter -= 1

                # Unlock the global mutex if this is the last unlock
                if counter == 0:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_UN)

            # Write the new counter value
            os.lseek(counter_fd, 0, os.SEEK_SET)
            os.ftruncate(counter_fd, 0)
            os.write(counter_fd, str(counter).encode())

            # Unlock the counter file
            fcntl.flock(counter_fd, fcntl.LOCK_UN)
            os.close(counter_fd)

            return True
        except (OSError, ValueError):
            print("Failed to lock mutex counter")
            return False


lock = LockManager()
