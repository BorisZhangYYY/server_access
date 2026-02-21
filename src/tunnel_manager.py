import os
import signal
import subprocess
from typing import Any, Dict, List, Optional

from base_manager import BaseManager


class TunnelManager(BaseManager):
    """Build remote SSH tunnels to local ports."""

    def __init__(self, config_path: str = "config.json"):
        super().__init__(config_path=config_path, config_key="tunnels", pid_tag="tunnel", log_tag="tunnel")

    def _get_server_config(self, alias: str) -> Optional[Dict[str, Any]]:
        return self._get_item_config(alias)

    def _get_ssh_base_cmd(self, server: Dict[str, Any]) -> List[str]:
        cmd = ["ssh"]
        jump_host = server.get("jump_host", "")
        if jump_host:
            user_host, port = jump_host.rsplit(":", 1)
            cmd.extend(["-p", port, user_host])
        return cmd

    def connect(self, alias: str) -> None:
        server = self._get_server_config(alias)
        if not server:
            print(f"Error: Tunnel config '{alias}' not found.")
            return

        print(f"Starting connection to '{alias}' ({server['host']})...")
        self.stop(alias)

        ssh_cmd = self._get_ssh_base_cmd(server) + [
            "-N",
            "-L",
            f"{server['local_port']}:{server['host']}:{server['remote_port']}",
        ] + server["tunnel_config"].split()

        print(f"Establishing SSH tunnel on port {server['local_port']}...")

        log_file = self._get_log_file(alias)
        try:
            with open(log_file, "w", encoding="utf-8") as log:
                process = subprocess.Popen(
                    ssh_cmd,
                    stdout=log,
                    stderr=log,
                    preexec_fn=os.setsid,
                )

            self._write_pid(alias, process.pid)
            print(f"Tunnel established (PID: {process.pid}).")
        except Exception as e:
            print(f"Error starting tunnel: {e}")

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
        print("\n=== Tunnel Status ===")
        print(f"{'Alias':<10} | {'Status':<10} | {'PID':<8}")
        print("-" * 60)

        for tunnel in self.config.get("tunnels", []):
            alias = tunnel["alias"]
            status, pid_str = self.pid_status(alias)
            print(f"{alias:<10} | {status:<10} | {pid_str:<8}")
        print("\n")

    def list_tunnels(self) -> List[str]:
        return self.get_aliases()
