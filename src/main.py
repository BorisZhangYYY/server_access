import sys
import argparse
from typing import List
from server_manager import ServerManager
from tunnel_manager import TunnelManager

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
            servers = manager[0].list_servers()
            tunnels = manager[1].list_tunnels()
            print("Available servers:", ", ".join(servers))
            print("Available tunnels:", ", ".join(tunnels))
        elif choice == '2':
            manager[0].status()
            manager[1].status()
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
            if alias and alias in manager[0].list_servers():
                manager[0].stop(alias)
            if alias and alias in manager[1].list_tunnels():
                manager[1].stop(alias)
        elif choice == 'q':
            sys.exit(0)
        else:
            print("Invalid choice.")

def main():
    manager = [ServerManager(), TunnelManager()]
    interactive_mode(manager)

if __name__ == "__main__":
    main()
