import os
import shutil
import subprocess


def cp_n(src, dst):
    """
    Copy a file from src to dst without overwriting if dst exists.
    Mimics the behavior of the shell script's cp_n function.
    """
    try:
        # Check if destination exists
        if os.path.exists(dst):
            print(f"File {dst} already exists, skipping copy")
            return False

        # Perform the copy
        shutil.copy2(src, dst)
        return True
    except (IOError, shutil.Error) as e:
        print(f"Error copying {src} to {dst}: {str(e)}")
        return False


def cp_n_busybox_fallback(src, dst):
    """
    Fallback implementation using busybox-style cp -n behavior.
    Uses subprocess to call the system's cp command if available.
    """
    try:
        # Try to use system's cp with -n option
        result = subprocess.run(['cp', '-n', src, dst],
                                check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to Python implementation if cp -n fails
        return cp_n(src, dst)


def cp_n_safe(src, dst):
    """
    Safe implementation that first checks for cp -n support.
    """
    try:
        # Check if cp supports -n option
        result = subprocess.run(['cp', '--help'],
                                check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)

        if '--no-clobber' in result.stdout:
            # Use cp -n if supported
            return cp_n_busybox_fallback(src, dst)
        else:
            # Fall back to Python implementation
            return cp_n(src, dst)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fall back to Python implementation if cp --help fails
        return cp_n(src, dst)
