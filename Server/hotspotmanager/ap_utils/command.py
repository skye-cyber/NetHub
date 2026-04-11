import subprocess
from .colors import fg


class CommandHelper:
    def __init__(self, cln_obj=None):
        self.clean = cln_obj

    def set_cleanup_manager(self, cln_obj):
        self.clean = cln_obj

    def run(
        self,
        cmd,
        check=True,
        capture_output=False,
        text=False,
        force_return=False
    ):
        """Run a command with proper error handling and sudo support"""
        try:
            # Check if we need sudo for this command
            privileged_commands = ['iptables', 'ip', 'iw', 'modprobe', 'systemctl', 'nmcli']
            if any(cmd[0].endswith(priv_cmd) for priv_cmd in privileged_commands):
                # Prepend sudo if not already present
                if not cmd[0] == 'sudo':
                    cmd = ['sudo'] + cmd
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=text
            )
            return result

        except subprocess.CalledProcessError as e:
            if force_return:
                print(f"\n{fg.FRED}Command failed{fg.RESET}: {fg.FWHITE}{' '.join(cmd)}{fg.RESET}")
                return {'status': 'error'}

            msg = f"Command failed: {' '.join(cmd)}"
            return self.error_handler(msg, self.clean)
        except Exception as e:
            msg = f"Error running command: {str(e)}: {' '.join(cmd)}"
            return self.error_handler(msg, self.clean)

    def error_handler(self, error, callback=None):
        self.clean.die(error) if self.clean else print(f"ERROR: {fg.RED}{error}{fg.RESET}")
        return False


command = CommandHelper()
