#!/bin/zsh

# 先检查并关闭已存在的隧道进程
pkill -f "ssh.*1143:localhost:1143" 2>/dev/null || true

# 远程启动code-server
ssh duser@172.26.24.88 << 'EOF'
    pkill -f 'code-server.*1143' 2>/dev/null || true
    
    cd /home/duser/huabei_manba/users/zhangdonghao/code-server-4.16.1-linux-amd64/
    nohup ./bin/code-server \
        --bind-addr 127.0.0.1:1143 \
        --auth none \
        > /dev/null 2>&1 &
    
    sleep 3
    echo "Code-server 已启动"
EOF

echo "正在建立 SSH 隧道..."
# 后台运行SSH隧道，记录PID
ssh -N -L 1143:localhost:1143 duser@172.26.24.88 &
TUNNEL_PID=$!

# 保存PID以便后续管理
echo $TUNNEL_PID > tunnel.pid

echo "访问地址：http://127.0.0.1:1143"
echo "隧道PID: $TUNNEL_PID (已保存到 tunnel.pid)"
echo "使用 './stop_tunnel.sh' 停止隧道"
