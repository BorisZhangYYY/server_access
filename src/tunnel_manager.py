import json
import os
import signal
import subprocess
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

class TunnelManager:
    """Build remote SSH tunnels to local ports."""

    def __init__(self, config_path: str = "config.json"):
        """Initializes the TunnelManager.

        Args:
            config_path: Path to the configuration file.
        """
        self.project_root = Path(__file__).parent.parent
        self.config_path = self.project_root / config_path
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Loads configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_server_config(self, alias: str) -> Optional[Dict[str, Any]]:
        """Retrieves configuration for a specific server alias."""
        for server in self.config.get("tunnels", []):
            if server["alias"] == alias:
                return server
        return None

    def _get_pid_file(self, alias: str) -> Path:
        """Returns the PID file path for a given server alias."""
        return self.logs_dir / f"{alias}.pid"
    
    def _get_ssh_base_cmd(self, server: Dict[str, Any]) -> List[str]:
        """Constructs the base SSH command with jump host if configured."""
        cmd = ["ssh"]
        jump_host = server.get("jump_host", "")
        if jump_host:
            user_host, port = jump_host.rsplit(":", 1)
            cmd.extend(["-p", port, user_host])
        return cmd
    
    def connect(self, alias: str) -> None:
        """Build a tunnel to a remote server.

        Args:
            alias: The alias of the tunnel to connect to.
        """
        server = self._get_server_config(alias)
        if not server:
            print(f"Error: Tunnel config '{alias}' not found.")
            return
        
        print(f"Starting connection to '{alias}' ({server['host']})...")

        # 1. Kill existing local tunnel for this specific configuration
        self.stop(alias)

        # 2. Construct the SSH command, example:
        # ssh -p 58422 liujiahao@jumper-huabei2-vpc.datagrand.com -N -f -L 23306:172.17.20.21:23306 -o TCPKeepAlive=yes
        ssh_cmd = self._get_ssh_base_cmd(server) + [
            "-N",  # No remote command (just forward ports)
            # "-f",  # Run in background
            "-L", f"{server['local_port']}:{server['host']}:{server['remote_port']}",
        ] + server['tunnel_config'].split()
        
        print(f"Establishing SSH tunnel on port {server['local_port']}...")

        # 3. Start the tunnel process
        # We use subprocess.Popen to start it in the background.
        log_file = self.logs_dir / f"{alias}_tunnel.log"
        
        try:
            with open(log_file, "w") as log:
                # preexec_fn=os.setsid makes the process a new session leader.
                # This ensures it doesn't get killed when the python script exits (if running interactively)
                # and allows it to run as a daemon-like process.
                process = subprocess.Popen(
                    ssh_cmd,
                    stdout=log,
                    stderr=log,
                    preexec_fn=os.setsid 
                )
            
            # Save PID so we can stop it later
            pid_file = self._get_pid_file(alias)
            with open(pid_file, "w") as f:
                f.write(str(process.pid))
            
            print(f"Tunnel established (PID: {process.pid}).")
            
        except Exception as e:
            print(f"Error starting tunnel: {e}")
            return

    def stop(self, alias: str) -> None:
        """Stops the SSH tunnel for a given server.

        Args:
            alias: The alias of the server to stop.
        """
        pid_file = self._get_pid_file(alias)
        if pid_file.exists():
            try:
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())
                
                try:
                    os.kill(pid, signal.SIGTERM)
                    print(f"Stopped tunnel for '{alias}' (PID: {pid}).")
                except ProcessLookupError:
                    print(f"Tunnel process for '{alias}' not found (PID: {pid}). Cleaning up PID file.")
                
                os.remove(pid_file)
            except Exception as e:
                print(f"Error stopping '{alias}': {e}")
        else:
            print(f"No active tunnel found for '{alias}'.")
        
    def status(self) -> None:
        """Prints the status of all configured tunnels."""
        print("\n=== Tunnel Status ===")
        print(f"{'Alias':<10} | {'Status':<10} | {'PID':<8}")
        print("-" * 60)

        for server in self.config.get("tunnels", []):
            alias = server["alias"]
            pid_file = self._get_pid_file(alias)
            status = "Stopped"
            pid_str = "-"

            if pid_file.exists():
                try:
                    with open(pid_file, "r") as f:
                        pid = int(f.read().strip())
                    # Check if process exists
                    try:
                        os.kill(pid, 0) # Signal 0 checks existence
                        status = "Running"
                        pid_str = str(pid)
                    except ProcessLookupError:
                        status = "Dead"
                        # Clean up dead PID file? Maybe not in status check, or yes.
                except ValueError:
                    status = "Error"

            print(f"{alias:<10} | {status:<10} | {pid_str:<8}")
        print("\n")
        
    def list_tunnels(self) -> list[str]:
        """Returns a list of tunnel aliases."""
        return [s["alias"] for s in self.config.get("tunnels", [])]