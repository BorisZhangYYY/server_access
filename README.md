# Server Manager

远程服务器管理工具，通过 SSH 隧道连接远程 Code Server 或搭建端口转发。

## 功能

### 1. 远程 Code Server 管理

- 一键启动远程服务器的 code-server
- 支持通过跳板机（Jump Host）连接
- 本地访问远程 Code Server：`http://127.0.0.1:<端口>`

### 2. SSH 隧道管理

- 支持端口转发（Local Port Forwarding）
- 支持跳板机（ProxyJump）
- 支持 TCPKeepAlive 保活机制
- 自动重连与进程管理

### 3. 工具集

- `reset_network.sh` - macOS 网络重置工具
- `register_ssh_hosts.py` - SSH Host 配置生成器
- `split_file.sh` - 文件分割工具

## 快速开始

### 1. 安装依赖

```bash
# 安装 code-server（以 v4.16.1 为例）
wget https://github.com/coder/code-server/releases/download/v4.16.1/code-server-4.16.1-linux-amd64.tar.gz
tar -xzf code-server-4.16.1-linux-amd64.tar.gz
cd code-server-4.16.1-linux-amd64
./bin/code-server --version
```

### 2. 配置

复制示例配置并修改：

```bash
cp config.json.example config.json
# 编辑 config.json，填入你的服务器信息
```

配置说明：

| 字段 | 说明 |
|------|------|
| `alias` | 服务器/隧道别名，用于菜单选择 |
| `host` | 服务器 IP 或域名 |
| `user` | SSH 用户名 |
| `local_port` | 本地监听端口 |
| `remote_port` | 远程服务端口 |
| `jump_host` | 跳板机地址，如 `user@bastion.com:22`，留空表示直连 |
| `remote_work_dir` | 远程服务器上 code-server 所在目录 |
| `start_cmd` | 启动 code-server 的命令 |
| `tunnel_config` | 额外的 SSH 选项，如 `-o TCPKeepAlive=yes` |

### 3. 运行

```bash
chmod +x server.sh
./server.sh
```

### 4. 使用菜单

```
=== Server Manager ===
1. List Servers                  - 列出所有服务器和隧道
2. Check Status                  - 查看运行状态
3. Connect to Code Server        - 连接 Code Server
4. Build Tunnel                  - 建立端口隧道
5. Stop Server&Tunnel Connection - 停止连接
q. Quit                          - 退出
```

## 项目结构

```
.
├── server.sh              # 入口脚本
├── config.json.example    # 配置示例
├── src/
│   ├── main.py            # 主程序
│   ├── base_manager.py    # 基础管理类
│   ├── server_manager.py  # Code Server 管理
│   └── tunnel_manager.py  # 隧道管理
└── tools/
    ├── reset_network.sh   # macOS 网络重置
    ├── register_ssh_hosts.py  # SSH 配置生成
    └── split_file.sh      # 文件分割
```

## 环境要求

- Python 3.6+
- SSH 客户端（OpenSSH）
- macOS / Linux

## 注意事项

- `config.json` 包含敏感信息，不要提交到代码仓库
- 确保 SSH 密钥已配置，可无密码登录远程服务器
