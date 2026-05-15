# Server Access

远程服务器管理工具，通过 SSH 隧道连接远程 Code Server 或搭建端口转发。

## 安装部署

```bash
# 克隆项目
git clone https://github.com/BorisZhangYYY/server_access.git
cd server_access

# 复制配置示例
cp config.json.example config.json

# 编辑配置，添加你的服务器信息
vim config.json
```

## 配置说明

配置文件：`config.json`

```json
{
    "servers": [
        {
            "alias": "my-server",
            "host": "192.168.1.100",
            "user": "ubuntu",
            "local_port": 1143,
            "remote_port": 1143,
            "jump_host": "",
            "remote_work_dir": "~/code-server/",
            "start_cmd": "nohup ./bin/code-server --bind-addr 127.0.0.1:1143 --auth none > /dev/null 2>&1 &"
        }
    ],
    "tunnels": [
        {
            "alias": "mysql",
            "host": "10.0.0.10",
            "local_port": 23306,
            "remote_port": 23306,
            "jump_host": "user@bastion.example.com:22",
            "tunnel_config": "-o TCPKeepAlive=yes"
        }
    ],
    "timeouts": {
        "connect_seconds": 15,
        "startup_check_seconds": 5,
        "server_alive_interval": 30,
        "server_alive_count_max": 5
    }
}
```

| 字段 | 说明 |
|------|------|
| `alias` | 服务器/隧道别名，用于 CLI 选择 |
| `host` | 服务器 IP 或域名 |
| `user` | SSH 用户名 |
| `local_port` | 本地监听端口 |
| `remote_port` | 远程服务端口 |
| `jump_host` | 跳板机地址，留空表示直连 |
| `remote_work_dir` | 远程服务器上 code-server 目录 |
| `start_cmd` | 启动 code-server 命令 |
| `tunnel_config` | 额外 SSH 选项 |

## CLI 命令

### 交互模式
```bash
./server.sh
```

### Agent 可用命令

**列出所有服务器和隧道：**
```bash
python3 src/main.py list
```

**查看所有连接状态：**
```bash
python3 src/main.py status
```

**连接 Code Server：**
```bash
python3 src/main.py connect <server_alias>
# 示例：python3 src/main.py connect my-server
```

**建立隧道：**
```bash
python3 src/main.py tunnel <tunnel_alias>
# 示例：python3 src/main.py tunnel mysql
```

**停止连接：**
```bash
python3 src/main.py stop <alias>
# 示例：python3 src/main.py stop my-server
# 示例：python3 src/main.py stop mysql
```

**注册 SSH Host 配置（生成 ~/.ssh/config 条目）：**
```bash
python3 tools/register_ssh_hosts.py
python3 tools/register_ssh_hosts.py --host <specific_host>  # 只注册特定主机
```

## 项目结构

```
.
├── server.sh              # 入口脚本
├── config.json            # 主配置
├── config.json.example    # 配置示例
├── src/
│   ├── main.py            # 主程序（CLI 入口）
│   ├── base_manager.py    # 基础管理类
│   ├── server_manager.py  # Code Server 管理
│   └── tunnel_manager.py  # 隧道管理
└── tools/
    ├── register_ssh_hosts.py  # SSH 配置生成器
    ├── reset_network.sh       # macOS 网络重置
    └── split_file.sh          # 文件分割
```

## 注意事项

- 确保 SSH 密钥已配置，可无密码登录远程服务器
- `config.json` 包含敏感信息，不应提交到代码仓库
- PID 文件存储在 `pids/` 目录
- 连接超时、存活检测等参数可在 `timeouts` 配置节中调整

## 使用场景

### 场景 1：连接到远程 Code Server

1. 配置 `config.json` 中的服务器信息
2. 运行 `python3 src/main.py connect <server_alias>`
3. 浏览器访问 `http://localhost:1143`

### 场景 2：建立数据库隧道

1. 配置 `config.json` 中的隧道信息
2. 运行 `python3 src/main.py tunnel <tunnel_alias>`
3. 本地访问 `localhost:23306` 即可连接远程数据库

### 场景 3：通过跳板机连接

在 `jump_host` 字段指定跳板机地址，例如：
```json
"jump_host": "user@bastion.example.com:22"
```
