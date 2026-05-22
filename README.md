# Server Manager

远程服务器管理工具：一键启动远程 Code Server 并建立本地隧道，或单独管理 SSH 端口转发。

## 功能

- **Code Server 管理**：SSH 到远程主机启动 code-server，建立本地隧道，浏览器访问 `http://127.0.0.1:<端口>`
- **SSH 隧道管理**：独立的端口转发（Local Port Forwarding），支持跳板机、TCPKeepAlive 保活
- **SSH Host 注册**：自动生成 `~/.ssh/config` 条目

## 安装 Code Server（远程服务器上执行）

```bash
# 下载（v4.16.1 适配较老 Linux 版本）
wget https://github.com/coder/code-server/releases/download/v4.16.1/code-server-4.16.1-linux-amd64.tar.gz

# 解压
tar -xzf code-server-4.16.1-linux-amd64.tar.gz

# 验证
cd code-server-4.16.1-linux-amd64
./bin/code-server --version
```

## 配置

```bash
cp config.json.example config.json
# 编辑 config.json
```

### Code Server 配置示例（`servers`）

```json
{
    "alias": "my-server",
    "host": "192.168.1.100",
    "user": "ubuntu",
    "local_port": 1143,
    "remote_port": 1143,
    "jump_host": "",
    "remote_work_dir": "/home/ubuntu/code-server-4.16.1-linux-amd64/",
    "start_cmd": "nohup ./bin/code-server --bind-addr 127.0.0.1:1143 --auth none > /dev/null 2>&1 &"
}
```

连接流程：`connect` 命令会先 SSH 登录远程主机，在 `remote_work_dir` 下执行 `start_cmd` 启动 code-server，然后在本地建立 `-L local_port:127.0.0.1:remote_port` 隧道。最后浏览器打开 `http://127.0.0.1:local_port`。

### 隧道配置示例（`tunnels`）

```json
{
    "alias": "mysql",
    "host": "10.0.0.10",
    "user": "ubuntu",
    "local_port": 23306,
    "remote_port": 3306,
    "jump_host": "user@bastion.example.com:22",
    "tunnel_config": "-o TCPKeepAlive=yes"
}
```

隧道只做端口转发，不在远程执行任何命令。

### 字段说明

| 字段 | 说明 |
|------|------|
| `alias` | 别名，用于 CLI 选择 |
| `host` | 服务器 IP 或域名 |
| `user` | SSH 用户名 |
| `local_port` | 本地监听端口 |
| `remote_port` | 远程服务端口 |
| `jump_host` | 跳板机，如 `user@bastion.com:22`，留空直连 |
| `remote_work_dir` | 远程 code-server 目录（仅 servers 需要） |
| `start_cmd` | 启动 code-server 的命令（仅 servers 需要） |
| `tunnel_config` | 额外 SSH 选项 |

## 使用

### 交互菜单

```bash
./server.sh
```

### CLI 命令

```bash
# 列出所有服务器和隧道
python3 src/main.py list

# 查看连接状态
python3 src/main.py status

# 连接 Code Server（启动 + 隧道）
python3 src/main.py connect <alias>

# 建立隧道（仅端口转发）
python3 src/main.py tunnel <alias>

# 停止连接
python3 src/main.py stop <alias>

# 注册 SSH Host 配置
python3 tools/register_ssh_hosts.py
```

## 环境要求

- Python 3.6+
- macOS / Linux
- 远程服务器需配置 SSH 密钥免密登录

## 注意事项

- `config.json` 含敏感信息，勿提交到仓库
- PID 文件存储在 `pids/` 目录
- 超时、保活参数在 `timeouts` 配置节调整
