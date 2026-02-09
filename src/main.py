import sys
import argparse
from typing import List
from server_manager import ServerManager

def interactive_mode(manager: ServerManager):
    """Runs the interactive menu."""
    while True:
        print("\n=== Code Server Manager ===")
        print("1. List Servers")
        print("2. Check Status")
        print("3. Connect to Server")
        print("4. Stop Server Connection")
        print("q. Quit")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == '1':
            servers = manager.list_servers()
            print("Available servers:", ", ".join(servers))
        elif choice == '2':
            manager.status()
        elif choice == '3':
            servers = manager.list_servers()
            print("Available servers:", ", ".join(servers))
            alias = input("Enter server alias to connect: ").strip()
            if alias:
                manager.connect(alias)
        elif choice == '4':
            servers = manager.list_servers()
            print("Available servers:", ", ".join(servers))
            alias = input("Enter server alias to stop: ").strip()
            if alias:
                manager.stop(alias)
        elif choice == 'q':
            sys.exit(0)
        else:
            print("Invalid choice.")

def main():
    parser = argparse.ArgumentParser(description="Manage remote code-servers.")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Connect command
    connect_parser = subparsers.add_parser("connect", help="Connect to a server")
    connect_parser.add_argument("alias", help="Server alias")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop a server connection")
    stop_parser.add_argument("alias", help="Server alias")

    # Status command
    subparsers.add_parser("status", help="Show status of all servers")

    # List command
    subparsers.add_parser("list", help="List available servers")

    args = parser.parse_args()
    manager = ServerManager()

    if args.command == "connect":
        manager.connect(args.alias)
    elif args.command == "stop":
        manager.stop(args.alias)
    elif args.command == "status":
        manager.status()
    elif args.command == "list":
        print("Available servers:", ", ".join(manager.list_servers()))
    else:
        # If no arguments provided, enter interactive mode
        interactive_mode(manager)

if __name__ == "__main__":
    main()
