- 2026.02.12
    1. mv reset_network.sh to tools/, and add a new tool called split_file.sh.
    2. develop new function to build remote tunnel to local port:
        1. update the file ./src/main.py to add a new option: "4. Build Tunnel" and put the next option numbers after it.
        2. add a file ./src/tunnel_manager.py to manage the tunnel configs in ./config.json.
        3. update the file ./src/main.py to import the tunnel_manager.py and complete the option logic of "4. Build Tunnel".
    3. test the new function "Build Tunnel" and make sure it works.
    4. other changes to make differences to ServerManager and TunnelManager, such as the logs' name and other text messages.

- 2026.02.22
    use ChatGPT-Codex to make a pull request for the project, the changes are listed as follows:
    1. add BaseManager to consolidate shared config/pid/log helpers, then let ServerManager and TunnelManager inherit from it.
    2. standardize pid/log filenames with tags (e.g. _server, _tunnel) and migrate legacy *.pid when detected.
    3. add cleanup of orphan pid/log files at startup when configs are removed (supports dry-run).
    4. unify status/pid checks via BaseManager.pid_status and list aliases via BaseManager.

- 2026.03.04
    1. i found that the log files of the system is always empty, so i decide to delete the function of writting log files.
    2. add new parameters in /config.json for tunnel timeout detection and keep-alive mechanism.

- TODO List:
    None for now.
