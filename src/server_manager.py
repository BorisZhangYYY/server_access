import os
import signal
import subprocess
from typing import Any, Dict, List, Optional

from base_manager import BaseManager


class ServerManager(BaseManager):
    """Manages remote code-server connections."""

    def __init__(self, config_path: str = "config.json"):
        super().__init__(config_path=config_path, config_key="servers", pid_tag="server", log_tag="server")

    def _get_server_config(self, alias: str) -> Optional[Dict[str, Any]]:
        return self._get_item_config(alias)

    def _get_ssh_base_cmd(self, server: Dict[str, Any]) -> List[str]:
        cmd = ["ssh"]
        if server.get("jump_host"):
            cmd.extend(["-J", server["jump_host"]])
        return cmd

    def connect(self, alias: str) -> None:
        server = self._get_server_config(alias)
        if not server:
            print(f"Error: Server '{alias}' not found in config.")
            return

        print(f"Starting connection to '{alias}' ({server['host']})...")
        self.stop(alias)

        print("Starting remote code-server...")
        remote_script = (
            f"cd {server['remote_work_dir']}\n"
            f"pkill -f 'code-server.*{server['remote_port']}' || true\n"
            f"{server['start_cmd']}\n"
            "sleep 2\n"
            "echo 'Remote initialization commands executed.'\n"
        )

        ssh_cmd = self._get_ssh_base_cmd(server) + [f"{server['user']}@{server['host']}"]

        try:
            process = subprocess.Popen(
                ssh_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
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

        print(f"Establishing SSH tunnel on port {server['local_port']}...")
        tunnel_cmd = self._get_ssh_base_cmd(server) + [
            "-N",
            "-L",
            f"{server['local_port']}:127.0.0.1:{server['remote_port']}",
            f"{server['user']}@{server['host']}",
        ]

        log_file = self._get_log_file(alias)
        with open(log_file, "w", encoding="utf-8") as log:
            process = subprocess.Popen(
                tunnel_cmd,
                stdout=log,
                stderr=log,
                preexec_fn=os.setsid,
            )

        self._write_pid(alias, process.pid)

        print(f"Tunnel established (PID: {process.pid}).")
        print(f"Access URL: http://127.0.0.1:{server['local_port']}")

    def stop(self, alias: str) -> None:
        pid = self._read_pid(alias)
        if pid is None:
            print(f"No active tunnel found for '{alias}'.")
            return

        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Stopped tunnel for '{alias}' (PID: {pid}).")
        except ProcessLookupError:
            print(f"Tunnel process for '{alias}' not found (PID: {pid}). Cleaning up PID file.")
        finally:
            self._remove_pid(alias)

    def status(self) -> None:
        print("\n=== Server Status ===")
        print(f"{'Alias':<10} | {'Status':<10} | {'PID':<8} | {'URL'}")
        print("-" * 60)

        for server in self.config.get("servers", []):
            alias = server["alias"]
            status, pid_str = self.pid_status(alias)
            url = f"http://127.0.0.1:{server['local_port']}" if status == "Running" else "-"
            print(f"{alias:<10} | {status:<10} | {pid_str:<8} | {url}")
        print("\n")

    def list_servers(self) -> List[str]:
        return self.get_aliases()
