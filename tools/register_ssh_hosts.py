"""Register SSH host settings derived from server/config.json into ~/.ssh/config.

This tool is intended for cases where:
- The project uses IPs in config.json; and
- You want SSH to pick the right `User` / `ProxyJump` without interactive password prompts.

It appends generated blocks to the end of ~/.ssh/config and marks them with:
`# build by server_tools`
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON content from a file path.

    Args:
        path: JSON file path.

    Returns:
        Parsed JSON object as dict.
    """
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _collect_hosts_to_register(config: Dict[str, Any]) -> Set[str]:
    """Collect unique tunnel hosts that should be registered.

    Args:
        config: Parsed server/config.json content.

    Returns:
        A set of host strings.
    """
    hosts: Set[str] = set()
    for tunnel in config.get("tunnels", []):
        host = tunnel.get("host")
        if isinstance(host, str) and host.strip():
            hosts.add(host.strip())
    return hosts


def _find_server_auth_for_host(config: Dict[str, Any], host: str) -> Tuple[Optional[str], Optional[str]]:
    """Find user and jump_host from servers section matching a host.

    Args:
        config: Parsed server/config.json content.
        host: Hostname or IP.

    Returns:
        (user, jump_host) if found; otherwise (None, None).
    """
    for server in config.get("servers", []):
        if server.get("host") == host:
            user = server.get("user")
            jump_host = server.get("jump_host")
            return (user if isinstance(user, str) and user.strip() else None,
                    jump_host if isinstance(jump_host, str) and jump_host.strip() else None)
    return (None, None)


def _build_host_block(alias: str, host: str, user: Optional[str], proxy_jump: Optional[str]) -> str:
    """Build a Host block text for ~/.ssh/config.

    Args:
        alias: Host stanza name (can be an IP).
        host: HostName value.
        user: Optional User value.
        proxy_jump: Optional ProxyJump value.

    Returns:
        SSH config block as text.
    """
    lines: List[str] = ["# build by server_tools", f"Host {alias}", f"  HostName {host}"]
    if user:
        lines.append(f"  User {user}")
    if proxy_jump:
        lines.append(f"  ProxyJump {proxy_jump}")
    return "\n".join(lines)


def _host_exists(ssh_config_text: str, alias: str) -> bool:
    """Check whether a Host stanza already exists.

    Args:
        ssh_config_text: Existing ~/.ssh/config content.
        alias: Host stanza name to look for.

    Returns:
        True if exists; otherwise False.
    """
    pattern = re.compile(rf"(?m)^\s*Host\s+{re.escape(alias)}(\s|$)")
    return pattern.search(ssh_config_text) is not None


def _append_blocks(ssh_config_path: Path, blocks: Sequence[str]) -> None:
    """Append blocks to the end of ~/.ssh/config with spacing requirements.

    The appended content ensures:
    - The new section is appended to the end of the file.
    - There is one blank line before the section and one blank line after.

    Args:
        ssh_config_path: ~/.ssh/config path.
        blocks: Blocks to append.
    """
    ssh_config_path.parent.mkdir(parents=True, exist_ok=True)
    content = ssh_config_path.read_text(encoding="utf-8") if ssh_config_path.exists() else ""

    if content and not content.endswith("\n"):
        content += "\n"

    to_append = "\n" + "\n\n".join(blocks) + "\n\n"
    ssh_config_path.write_text(content + to_append, encoding="utf-8")


def register_from_config(config_path: Path, host_filter: Optional[str]) -> List[str]:
    """Generate host blocks to be registered.

    Args:
        config_path: server/config.json path.
        host_filter: Optional filter to register only one host.

    Returns:
        A list of blocks to append.
    """
    config = _load_json(config_path)
    hosts = _collect_hosts_to_register(config)
    if host_filter:
        hosts = {host_filter} if host_filter in hosts else {host_filter}

    blocks: List[str] = []
    ssh_config_path = Path.home() / ".ssh" / "config"
    existing = ssh_config_path.read_text(encoding="utf-8") if ssh_config_path.exists() else ""

    for host in sorted(hosts):
        if _host_exists(existing, host):
            continue
        user, jump_host = _find_server_auth_for_host(config, host)
        block = _build_host_block(alias=host, host=host, user=user, proxy_jump=jump_host)
        blocks.append(block)

    return blocks


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        argv: Optional argv override.

    Returns:
        Parsed namespace.
    """
    default_config_path = Path(__file__).resolve().parents[1] / "config.json"
    parser = argparse.ArgumentParser(description="Register SSH hosts into ~/.ssh/config")
    parser.add_argument(
        "--config",
        dest="config_path",
        type=Path,
        default=default_config_path,
        help="Path to server/config.json",
    )
    parser.add_argument(
        "--host",
        dest="host",
        type=str,
        default=None,
        help="Only register a specific host (IP or hostname).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI entrypoint."""
    args = parse_args(argv)
    blocks = register_from_config(args.config_path, args.host)
    if not blocks:
        return
    ssh_config_path = Path.home() / ".ssh" / "config"
    _append_blocks(ssh_config_path, blocks)


if __name__ == "__main__":
    main()
