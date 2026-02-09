#!/bin/zsh
LOG_DIR="$HOME/Desktop/server/logs"
mkdir -p $LOG_DIR
DATE=$(date +%Y%m%d_%H%M%S)

echo "=== 启动代码服务器 ($DATE) ===" >> $LOG_DIR/server.log

nohup ~/Desktop/server/run_server.sh \
    1>$LOG_DIR/server_normal_$DATE.log \
    2>$LOG_DIR/server_error_$DATE.log &

SERVER_PID=$!
echo $SERVER_PID > $LOG_DIR/server.pid
echo "服务器启动中... (PID: $SERVER_PID)"
echo "日志目录: $LOG_DIR"
