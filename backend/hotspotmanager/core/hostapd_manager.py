import subprocess
import os
import time
from ap_utils.config import config_manager
from pathlib import Path


class HostapdManager:
    def __init__(self, config=None):
        self.config = config_manager.get_config
        self.config_file = (Path(self.config['conf_dir']) / "hostapd.conf").as_posix()
        self.script_path = (Path(self.config['base_prog_dir']) / Path(__file__).parent / "hostapd_helper.sh").as_posix()
        self.pid_file = Path(self.config['proc_dir']) / "hostapd.pid"
        self.log_file = Path(self.config['base_dir']) / "hostapd.log"
        # Ensure script exists
        self._ensure_script()

    def _ensure_script(self):
        """Ensure the bash script exists and is executable"""
        if not os.path.exists(self.script_path):
            # Create the script (you would deploy it separately)
            raise FileNotFoundError(
                f"Hostapd script not found at {self.script_path}. "
                "Please install the script first."
            )

        # Make executable
        os.chmod(self.script_path, 0o755)

    def _run_script(self, action, extra_args=None):
        """Run the bash script with given action"""
        cmd = [self.script_path, action]

        # Add config-specific args
        if self.config.get('daemon', True):
            cmd.append("--daemon")

        if self.config.get('hostapd_debug', False):
            cmd.append("--debug")

        if self.config.get('vwifi_iface'):
            cmd.append(f"--interface={self.config['vwifi_iface']}")

        cmd.append(f"--config={self.config_file}")
        # cmd.append(f"--log={self.log_file}")

        # Add extra args
        if extra_args:
            cmd.extend(extra_args)

        try:
            os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin'
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"{e.stderr}\nExit code: {e.returncode}"

    def start(self):
        """Start hostapd"""
        print("Starting hostapd via bash script...")
        success, output = self._run_script("start")

        if success:
            print(f"✅ {output.strip()}")

            # Wait and verify
            time.sleep(1)
            if self.is_running():
                return True
            else:
                print("⚠️  hostapd started but PID not found")
                return False
        else:
            print(f"❌ Failed to start hostapd:\n{output}")
            return False

    def stop(self):
        """Stop hostapd"""
        print("Stopping hostapd...")
        success, output = self._run_script("stop")

        if success:
            print(f"✅ {output.strip()}")
            return True
        else:
            print(f"❌ Failed to stop hostapd:\n{output}")
            return False

    def restart(self):
        """Restart hostapd"""
        print("Restarting hostapd...")
        success, output = self._run_script("restart")

        if success:
            print(f"✅ {output.strip()}")
            return True
        else:
            print(f"❌ Failed to restart hostapd:\n{output}")
            return False

    def status(self):
        """Check hostapd status"""
        success, output = self._run_script("status")

        if success:
            status_text = output.strip()
            if "running" in status_text.lower():
                return True, status_text
            else:
                return False, status_text
        else:
            return False, output

    def reload(self):
        """Reload hostapd configuration"""
        print("Reloading hostapd config...")
        success, output = self._run_script("reload")

        if success:
            print(f"✅ {output.strip()}")
            return True
        else:
            print(f"❌ Failed to reload config:\n{output}")
            return False

    def is_running(self):
        """Check if hostapd is running"""
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())

                # Check if process exists
                os.kill(pid, 0)
                return True
            except (ValueError, OSError, FileNotFoundError):
                return False
        return False

    def get_pid(self):
        """Get hostapd PID"""
        if self.is_running():
            with open(self.pid_file, 'r') as f:
                return int(f.read().strip())
        return None

    def follow_logs(self, lines=50):
        """Follow hostapd logs"""
        try:
            if not os.path.exists(self.log_file):
                print(f"No log file found: {self.log_file}")
                return False

            # Show last N lines
            subprocess.run(["tail", f"-n{lines}", self.log_file])

            # Optionally follow (uncomment if desired)
            # print("\nFollowing logs (Ctrl+C to stop)...")
            # subprocess.run(["tail", "-f", self.log_file])

            return True
        except Exception as e:
            print(f"Error reading logs: {e}")
            return False

    def update_config(self, config_updates):
        """Update hostapd config and reload"""
        config_path = self.config.get('hostapd_config',
                                      '/etc/ap_manager/conf/hostapd.conf')

        try:
            # Read current config
            with open(config_path, 'r') as f:
                lines = f.readlines()

            # Apply updates
            updated_lines = []
            for line in lines:
                updated = False
                for key, value in config_updates.items():
                    if line.strip().startswith(f"{key}="):
                        updated_lines.append(f"{key}={value}\n")
                        updated = True
                        break
                if not updated:
                    updated_lines.append(line)

            # Add new keys not already present
            existing_keys = {line.split('=')[0].strip()
                             for line in lines if '=' in line}
            for key, value in config_updates.items():
                if key not in existing_keys:
                    updated_lines.append(f"{key}={value}\n")

            # Write updated config
            with open(config_path, 'w') as f:
                f.writelines(updated_lines)

            print(f"✅ Config updated: {config_updates}")

            # Reload if running
            if self.is_running():
                return self.reload()

            return True

        except Exception as e:
            print(f"❌ Failed to update config: {e}")
            return False


hostapdmanager = HostapdManager()
