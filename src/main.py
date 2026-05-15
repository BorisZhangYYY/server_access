import argparse
import sys
from typing import List
from server_manager import ServerManager
from tunnel_manager import TunnelManager


def list_all(manager: [ServerManager, TunnelManager]) -> None:
    """List all servers and tunnels."""
    servers = manager[0].list_servers()
    tunnels = manager[1].list_tunnels()
    print("Servers:", ", ".join(servers) if servers else "(none)")
    print("Tunnels:", ", ".join(tunnels) if tunnels else "(none)")


def show_status(manager: [ServerManager, TunnelManager]) -> None:
    """Show status of all servers and tunnels."""
    manager[0].status()
    manager[1].status()


def connect_server(manager: [ServerManager, TunnelManager], alias: str) -> None:
    """Connect to a code server by alias."""
    if not alias:
        print("Error: alias required")
        return
    manager[0].connect(alias)


def build_tunnel(manager: [ServerManager, TunnelManager], alias: str) -> None:
    """Build a tunnel by alias."""
    if not alias:
        print("Error: alias required")
        return
    manager[1].connect(alias)


def stop_connection(manager: [ServerManager, TunnelManager], alias: str) -> None:
    """Stop a server or tunnel by alias."""
    if not alias:
        print("Error: alias required")
        return
    servers = manager[0].list_servers()
    tunnels = manager[1].list_tunnels()
    if alias in servers:
        manager[0].stop(alias)
    elif alias in tunnels:
        manager[1].stop(alias)
    else:
        print(f"Error: alias '{alias}' not found")


def interactive_mode(manager: [ServerManager, TunnelManager]):
    """Runs the interactive menu."""
    while True:
        print("\n=== Server Manager ===")
        print("1. List Servers")
        print("2. Check Status")
        print("3. Connect to Code Server")
        print("4. Build Tunnel")
        print("5. Stop Server&Tunnel Connection")
        print("q. Quit")

        choice = input("\nEnter choice: ").strip().lower()

        if choice == '1':
            list_all(manager)
        elif choice == '2':
            show_status(manager)
        elif choice == '3':
            servers = manager[0].list_servers()
            print("Available code servers:", ", ".join(servers))
            alias = input("Enter code server alias to connect: ").strip()
            if alias:
                manager[0].connect(alias)
        elif choice == '4':
            tunnels = manager[1].list_tunnels()
            print("Available tunnels:", ", ".join(tunnels))
            alias = input("Enter tunnel alias to build: ").strip()
            if alias:
                manager[1].connect(alias)
        elif choice == '5':
            alias = input("Enter server&tunnel to stop: ").strip()
            if alias:
                stop_connection(manager, alias)
        elif choice == 'q':
            sys.exit(0)
        else:
            print("Invalid choice.")


def main():
    manager = [ServerManager(), TunnelManager()]

    parser = argparse.ArgumentParser(description="Server Manager - Manage remote code servers and SSH tunnels")
    sub = parser.add_subparsers(dest="command", required=False)

    sub.add_parser("list", help="List all servers and tunnels")
    sub.add_parser("status", help="Show status of all connections")

    connect_p = sub.add_parser("connect", help="Connect to a code server")
    connect_p.add_argument("alias", help="Server alias")

    tunnel_p = sub.add_parser("tunnel", help="Build a tunnel")
    tunnel_p.add_argument("alias", help="Tunnel alias")

    stop_p = sub.add_parser("stop", help="Stop a server or tunnel")
    stop_p.add_argument("alias", help="Server or tunnel alias")

    args = parser.parse_args()

    if args.command == "list":
        list_all(manager)
    elif args.command == "status":
        show_status(manager)
    elif args.command == "connect":
        connect_server(manager, args.alias)
    elif args.command == "tunnel":
        build_tunnel(manager, args.alias)
    elif args.command == "stop":
        stop_connection(manager, args.alias)
    else:
        interactive_mode(manager)

if __name__ == "__main__":
    main()
