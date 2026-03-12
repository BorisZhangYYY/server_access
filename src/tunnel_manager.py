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
        """Create an SSH local port forward tunnel.

        Args:
            alias: Tunnel alias in config.

        The connection is attempted in two phases:
        1) Forward to the tunnel's configured host (legacy behavior).
        2) Forward to 127.0.0.1 on the remote (common for services bound locally).

        If both attempts fail, the user will be guided to register SSH host config
        via the provided server tools script.
        """
        server = self._get_server_config(alias)
        if not server:
            print(f"Error: Tunnel config '{alias}' not found.")
            return

        print(f"Starting connection to '{alias}' ({server['host']})...")
        self.stop(alias)

        dest_user = server.get("user")
        dest = f"{dest_user}@{server['host']}" if dest_user else f"{server['host']}"
        tunnel_config_tokens = str(server.get("tunnel_config", "")).split()

        remote_hosts_to_try = [str(server["host"]), "127.0.0.1"]
        last_stderr = ""

        for index, remote_bind_host in enumerate(remote_hosts_to_try, start=1):
            ssh_cmd = self._get_ssh_base_cmd(server) + [
                "-N",
                "-o",
                "ExitOnForwardFailure=yes",
                "-L",
                f"{server['local_port']}:{remote_bind_host}:{server['remote_port']}",
            ] + tunnel_config_tokens + [dest]

            mode = "remote-host" if index == 1 else "remote-127.0.0.1"
            print(
                f"Establishing SSH tunnel on port {server['local_port']} "
                f"(mode: {mode})..."
            )

            try:
                process = subprocess.Popen(
                    ssh_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    preexec_fn=os.setsid,
                )
                time.sleep(self.STARTUP_CHECK_SECONDS)
                if process.poll() is not None:
                    stderr_text = ""
                    if process.stderr is not None:
                        stderr_text = (process.stderr.read() or "").strip()
                    if stderr_text:
                        last_stderr = stderr_text
                        print(stderr_text)
                    continue

                self._write_pid(alias, process.pid)
                print(f"Tunnel established (PID: {process.pid}).")
                return
            except Exception as e:
                last_stderr = str(e)
                continue

        print(f"Error: failed to establish tunnel for '{alias}'.")
        if last_stderr:
            print(last_stderr)
        script_path = str(self.project_root / "tools" / "register_ssh_hosts.py")
        print(
            "Hint: If you rely on ~/.ssh/config (e.g. correct User/ProxyJump), "
            f"run:\n  python3 {script_path}"
        )

    def stop(self, alias: str) -> None:
        pid = self._read_pid(alias)
        if pid is None:
            print(f"No active tunnel found for '{alias}'.")
            return

        server = self._get_server_config(alias)
        required_tokens = ["ssh"]
        if server and server.get("local_port") is not None:
            required_tokens.append(f"-L {server['local_port']}:")
        required_tokens.append("ExitOnForwardFailure=yes")

        try:
            if not self._pid_matches_expected_command(pid, required_tokens):
                print(
                    f"PID {pid} for '{alias}' does not look like a tunnel process. "
                    "Cleaning up PID file without killing."
                )
                return
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
