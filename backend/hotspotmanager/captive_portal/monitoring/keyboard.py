# Install: pip install keyboard
import keyboard
import threading


class KeyboardHandler:
    """Non-blocking keyboard input without curses"""

    def __init__(self, monitor):
        self.monitor = monitor
        self.running = True
        self.thread = None

    def start(self):
        """Start keyboard listener in background thread"""
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        print("✓ Keyboard handler started (↑↓ jk: navigate, a: auth, b: block, q: quit)")

    def _listen(self):
        """Listen for keyboard events"""
        try:
            # Map keys to actions
            key_map = {
                'up': lambda: self._move_selection(-1),
                'down': lambda: self._move_selection(1),
                'j': lambda: self._move_selection(1),
                'k': lambda: self._move_selection(-1),
                'a': self._authenticate_selected,
                'b': self._block_selected,
                'r': self._refresh,
                'q': self._quit
            }

            while self.running:
                # Wait for key press (non-blocking check)
                for key in key_map:
                    if keyboard.is_pressed(key):
                        key_map[key]()
                        time.sleep(0.2)  # Debounce

                time.sleep(0.05)  # Small delay to prevent CPU overload

        except Exception as e:
            print(f"Keyboard error: {e}")

    def _move_selection(self, direction):
        """Move selection up/down"""
        with self.monitor.devices_lock:
            device_count = len(self.monitor.devices)

        if device_count > 0:
            new_index = self.monitor.selected_index + direction
            # Wrap around
            if new_index < 0:
                new_index = device_count - 1
            elif new_index >= device_count:
                new_index = 0

            self.monitor.selected_index = new_index

    def _authenticate_selected(self):
        """Authenticate selected device"""
        with self.monitor.devices_lock:
            devices = list(self.monitor.devices.values())

        if devices and 0 <= self.monitor.selected_index < len(devices):
            device = devices[self.monitor.selected_index]
            self.monitor.toggle_device_auth(device.mac)

    def _block_selected(self):
        """Block selected device - same as authenticate (toggle)"""
        self._authenticate_selected()

    def _refresh(self):
        """Manual refresh"""
        self.monitor._perform_scan()

    def _quit(self):
        """Quit application"""
        self.monitor.running = False
