import os
import signal
import subprocess
import time
from typing import Any, Dict, List, Optional

from base_manager import BaseManager


class TunnelManager(BaseManager):
    """Build remote SSH tunnels to local ports."""

    CONNECT_TIMEOUT_SECONDS = 15
    STARTUP_CHECK_SECONDS = 2
    SERVER_ALIVE_INTERVAL = 15
    SERVER_ALIVE_COUNT_MAX = 2

    def __init__(self, config_path: str = "config.json"):
        super().__init__(config_path=config_path, config_key="tunnels", pid_tag="tunnel")
        timeouts = self.config.get("timeouts", {})
        self.CONNECT_TIMEOUT_SECONDS = int(timeouts.get("connect_seconds", self.CONNECT_TIMEOUT_SECONDS))
        self.STARTUP_CHECK_SECONDS = int(timeouts.get("startup_check_seconds", self.STARTUP_CHECK_SECONDS))
        self.SERVER_ALIVE_INTERVAL = int(timeouts.get("server_alive_interval", self.SERVER_ALIVE_INTERVAL))
        self.SERVER_ALIVE_COUNT_MAX = int(timeouts.get("server_alive_count_max", self.SERVER_ALIVE_COUNT_MAX))

    def _get_server_config(self, alias: str) -> Optional[Dict[str, Any]]:
        return self._get_item_config(alias)

    def _get_ssh_base_cmd(self, server: Dict[str, Any]) -> List[str]:
        cmd = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            f"ConnectTimeout={self.CONNECT_TIMEOUT_SECONDS}",
            "-o",
            f"ServerAliveInterval={self.SERVER_ALIVE_INTERVAL}",
            "-o",
            f"ServerAliveCountMax={self.SERVER_ALIVE_COUNT_MAX}",
        ]
        jump_host = server.get("jump_host", "")
        if jump_host:
            cmd.extend(["-J", jump_host])
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
            "-o",
            "ExitOnForwardFailure=yes",
            "-L",
            f"{server['local_port']}:{server['host']}:{server['remote_port']}",
        ] + server["tunnel_config"].split()

        print(f"Establishing SSH tunnel on port {server['local_port']}...")

        try:
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid,
            )
            time.sleep(self.STARTUP_CHECK_SECONDS)
            if process.poll() is not None:
                print(f"Error: failed to establish tunnel for '{alias}'.")
                return
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
