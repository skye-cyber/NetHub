import threading
import sys
import termios
import tty
import select


class SimpleKeyboardHandler:
    """Simple keyboard input using terminal settings"""

    def __init__(self, monitor):
        self.monitor = monitor
        self.running = True
        self.thread = None

    def start(self):
        """Start keyboard listener"""
        # Save terminal settings
        self.old_settings = termios.tcgetattr(sys.stdin)

        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        print("✓ Keyboard: ↑↓/jk=nav, a/auth, b/block, q/quit")

    def _listen(self):
        """Listen for keyboard input"""
        try:
            # Set terminal to non-blocking mode
            tty.setcbreak(sys.stdin.fileno())

            while self.running and self.monitor.running:
                # Check if input is available (non-blocking)
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    self._handle_char(char)

        except Exception as e:
            print(f"Keyboard error: {e}")
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def _handle_char(self, char):
        """Handle single character input"""
        char = char.lower()

        if char == 'q':
            self.monitor.running = False
        elif char == 'a':
            self._authenticate_selected()
        elif char == 'b':
            self._block_selected()
        elif char == 'r':
            self.monitor._perform_scan()
        elif char == 'j':
            self._move_selection(1)
        elif char == 'k':
            self._move_selection(-1)
        elif char == '\x1b':  # Escape sequence (arrows)
            # Read more chars for arrow keys
            if select.select([sys.stdin], [], [], 0.01)[0]:
                next_chars = sys.stdin.read(2)
                if next_chars == '[A':  # Up arrow
                    self._move_selection(-1)
                elif next_chars == '[B':  # Down arrow
                    self._move_selection(1)

    def _move_selection(self, direction):
        """Move selection"""
        with self.monitor.devices_lock:
            device_count = len(self.monitor.devices)

        if device_count > 0:
            new_index = self.monitor.selected_index + direction
            new_index = max(0, min(new_index, device_count - 1))
            self.monitor.selected_index = new_index

    def _authenticate_selected(self):
        """Authenticate selected device"""
        with self.monitor.devices_lock:
            devices = list(self.monitor.devices.values())

        if devices and 0 <= self.monitor.selected_index < len(devices):
            device = devices[self.monitor.selected_index]
            self.monitor.toggle_device_auth(device.mac)

    def _block_selected(self):
        """Block selected device"""
        self._authenticate_selected()
