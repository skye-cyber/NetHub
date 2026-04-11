import signal
import sys
import os
from typing import Optional
from ap_utils.colors import fg


class SignalHandler:
    def __init__(self, config=None):
        self.config = config
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Setup signal handlers for the application."""
        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGUSR1, self.handle_signal)
        signal.signal(signal.SIGUSR2, self.handle_signal)

        # Store original signal handlers for cleanup
        self.original_sigint_handler = signal.getsignal(signal.SIGINT)
        self.original_sigusr1_handler = signal.getsignal(signal.SIGUSR1)
        self.original_sigusr2_handler = signal.getsignal(signal.SIGUSR2)

    def handle_signal(self, signum, frame):
        """Handle signals received by the application."""
        if signum == signal.SIGINT:
            sys.exit(1)
        if signum == signal.SIGUSR1:
            self.clean_exit()
        elif signum == signal.SIGUSR2:
            self.die()

    def cleanup(self):
        """To be implemented"""

    def clean_exit(self, message: Optional[str] = None):
        """Handle clean exits."""
        if message:
            print(message)

        '''
        Send die signal to the main process if not the main process
        Only when runing in daemon mode eg ap_manager command never existed so not applicable in current implementation
        '''
        # if os.getpid() != os.getppid():
        #     os.kill(os.getppid(), signal.SIGUSR2)

        # Restore original signal handlers
        signal.signal(signal.SIGINT, self.original_sigint_handler)
        signal.signal(signal.SIGUSR1, self.original_sigusr1_handler)
        signal.signal(signal.SIGUSR2, self.original_sigusr2_handler)

        # Perform cleanup
        self.cleanup()

        # Wifi restart
        self.ap_man.netmanager.wifi_switch(state="off")
        self.ap_man.netmanager.wifi_switch(state="on")

        # Exit with success status
        sys.exit(0)

    def die(self, message: Optional[str] = None):
        """Handle fatal errors and exit."""
        if message:
            print(f"\nERROR: {fg.RED}{message}{fg.RESET}\n", file=sys.stderr)

        # Send die signal to the main process if not the main process
        if os.getpid() != os.getppid():
            pass  # os.kill(os.getppid(), signal.SIGUSR2)

        # Restore original signal handlers
        try:
            signal.signal(signal.SIGINT, self.original_sigint_handler)
            signal.signal(signal.SIGUSR1, self.original_sigusr1_handler)
            signal.signal(signal.SIGUSR2, self.original_sigusr2_handler)
        except Exception:
            pass

        # Perform cleanup
        self.cleanup()

        # Exit with error status
        sys.exit(1)
