#!/bin/zsh

case "$1" in
    start)
        echo "启动服务..."
        ~/Desktop/server/server_connect.sh
        ;;
    stop)
        echo "停止服务..."
        if [ -f ~/Desktop/server/logs/server.pid ]; then
            PID=$(cat ~/Desktop/server/logs/server.pid)
            kill $PID 2>/dev/null && echo "已停止服务器进程"
            rm -f ~/Desktop/server/logs/server.pid
        fi
        ~/Desktop/server/stop_tunnel.sh
        ;;
    status)
        echo "=== 服务状态 ==="
	    current_status=0
        # 检查隧道
        if [ -f ~/Desktop/server/tunnel.pid ]; then
            TUNNEL_PID=$(cat ~/Desktop/server/tunnel.pid)
            if ps -p $TUNNEL_PID > /dev/null; then
		current_status=1
                echo "✓ SSH隧道运行中 (PID: $TUNNEL_PID)"
            else
                echo "✗ SSH隧道未运行"
            fi
        else
            echo "✗ SSH隧道未运行"
        fi
        
        # 检查远程服务
        echo -n "远程code-server: "
	if [ $current_status -eq 1 ]; then
            ssh duser@172.26.24.88 "pgrep -f 'code-server.*1143' >/dev/null && echo '✓ 运行中' || echo '✗ 未运行'"
    else
        echo "✗ 无法链接（隧道未运行）"
	fi
        ;;
    logs)
        tail -f ~/Desktop/server/logs/server_normal_*.log
        ;;
    *)
        echo "用法: $0 {start|stop|status|logs}"
        exit 1
        ;;
esac
