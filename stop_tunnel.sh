#!/bin/zsh
if [ -f tunnel.pid ]; then
    PID=$(cat tunnel.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        echo "已停止隧道进程 (PID: $PID)"
    else
        echo "隧道进程不存在"
    fi
    rm -f tunnel.pid
else
    echo "未找到 tunnel.pid 文件"
fi
