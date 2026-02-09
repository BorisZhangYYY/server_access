import json
import os
import subprocess
import time
import signal
from typing import Dict, List, Optional, Any
from pathlib import Path

class ServerManager:
    """Manages remote code-server connections and SSH tunnels."""

    def __init__(self, config_path: str = "config.json"):
        """Initializes the ServerManager.

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
        for server in self.config.get("servers", []):
            if server["alias"] == alias:
                return server
        return None

    def _get_pid_file(self, alias: str) -> Path:
        """Returns the PID file path for a given server alias."""
        return self.logs_dir / f"{alias}.pid"

    def _get_ssh_base_cmd(self, server: Dict[str, Any]) -> List[str]:
        """Constructs the base SSH command with jump host if configured."""
        cmd = ["ssh"]
        if server.get("jump_host"):
            cmd.extend(["-J", server["jump_host"]])
        return cmd

    def connect(self, alias: str) -> None:
        """Connects to a server: starts remote process and establishes local tunnel.

        Args:
            alias: The alias of the server to connect to.
        """
        server = self._get_server_config(alias)
        if not server:
            print(f"Error: Server '{alias}' not found in config.")
            return

        print(f"Starting connection to '{alias}' ({server['host']})...")

        # 1. Kill existing local tunnel for this specific configuration
        self.stop(alias)

        # 2. Start remote code-server
        print("Starting remote code-server...")
        
        # Construct a script to be executed on the remote server
        # We use a script passed via stdin to ensure better handling of background processes
        remote_script = (
            f"cd {server['remote_work_dir']}\n"
            f"pkill -f 'code-server.*{server['remote_port']}' || true\n"
            f"{server['start_cmd']}\n"
            "sleep 2\n" # Give nohup time to detach
            "echo 'Remote initialization commands executed.'\n"
        )
        
        ssh_cmd = self._get_ssh_base_cmd(server) + [f"{server['user']}@{server['host']}"]

        try:
            # Use Popen to pipe the script to stdin, mimicking 'ssh user@host << EOF'
            process = subprocess.Popen(
                ssh_cmd, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=remote_script)
            
            if process.returncode != 0:
                print(f"Error executing remote commands. Exit code: {process.returncode}")
                print(f"Stderr: {stderr}")
                return
            
            print("Remote code-server started (or attempted). Output:")
            print(stdout)
            
        except Exception as e:
            print(f"Error starting remote server: {e}")
            return

        # 3. Establish SSH Tunnel
        print(f"Establishing SSH tunnel on port {server['local_port']}...")
        tunnel_cmd = self._get_ssh_base_cmd(server) + [
            "-N",  # Do not execute a remote command
            "-L", f"{server['local_port']}:127.0.0.1:{server['remote_port']}",
            f"{server['user']}@{server['host']}"
        ]

        log_file = self.logs_dir / f"{alias}_tunnel.log"
        with open(log_file, "w") as log:
            process = subprocess.Popen(
                tunnel_cmd,
                stdout=log,
                stderr=log,
                preexec_fn=os.setsid # Create new process group
            )
        
        # Save PID
        pid_file = self._get_pid_file(alias)
        with open(pid_file, "w") as f:
            f.write(str(process.pid))
        
        print(f"Tunnel established (PID: {process.pid}).")
        print(f"Access URL: http://127.0.0.1:{server['local_port']}")

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
        """Prints the status of all configured servers."""
        print("\n=== Server Status ===")
        print(f"{'Alias':<10} | {'Status':<10} | {'PID':<8} | {'URL'}")
        print("-" * 60)

        for server in self.config.get("servers", []):
            alias = server["alias"]
            pid_file = self._get_pid_file(alias)
            status = "Stopped"
            pid_str = "-"
            url = "-"

            if pid_file.exists():
                try:
                    with open(pid_file, "r") as f:
                        pid = int(f.read().strip())
                    # Check if process exists
                    try:
                        os.kill(pid, 0) # Signal 0 checks existence
                        status = "Running"
                        pid_str = str(pid)
                        url = f"http://127.0.0.1:{server['local_port']}"
                    except ProcessLookupError:
                        status = "Dead"
                        # Clean up dead PID file? Maybe not in status check, or yes.
                except ValueError:
                    status = "Error"

            print(f"{alias:<10} | {status:<10} | {pid_str:<8} | {url}")
        print("\n")

    def list_servers(self) -> List[str]:
        """Returns a list of server aliases."""
        return [s["alias"] for s in self.config.get("servers", [])]
