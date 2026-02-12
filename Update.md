- 2026.02.12
    1. mv reset_network.sh to tools/, and add a new tool called split_file.sh.
    2. develop new function to build remote tunnel to local port:
        1. update the file ./src/main.py to add a new option: "4. Build Tunnel" and put the next option numbers after it.
        2. add a file ./src/tunnel_manager.py to manage the tunnel configs in ./config.json.
        3. update the file ./src/main.py to import the tunnel_manager.py and complete the option logic of "4. Build Tunnel".
    3. test the new function "Build Tunnel" and make sure it works.
    4. other changes to make differences to ServerManager and TunnelManager, such as the logs' name and other text messages.

- TODO IN FUTURE:
    1. folder logs have some old files, need to clean them. and need to add some logic, if the server config is gone or the tunnel config is gone, then the log file should be deleted.
    2. i think the two managers have many duplicated code, mabbe in the future we can reafctor them into a base class, such as BaseManager, and let ServerManager and TunnelManager inherit from it.
    3. i think that the log file is no use because there are not logics to write logs to it, so maybe we can remove it or add some logics to write logs to it.