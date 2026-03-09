#!/bin/bash

echo "开始重置 macOS 网络设置..."

# 1. 刷新 DNS 缓存
echo "刷新 DNS 缓存..."
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# 2. 获取网络接口名称 (例如 en0, en1)
# 优先获取默认路由使用的接口，如果失败则默认为 en0
iface="$(route get default 2>/dev/null | awk '/interface:/{print $2; exit}')"
if [ -z "$iface" ]; then
    iface="en0"
fi
echo "目标网络接口: $iface"

# 3. 重启网络接口
echo "重启网络接口..."
sudo ifconfig "$iface" down
sleep 2
sudo ifconfig "$iface" up

# 4. 续订 DHCP 租约
echo "续订 DHCP 租约..."
# 直接使用 DHCP 模式，系统会自动处理释放和重新获取
sudo ipconfig set "$iface" DHCP

# 5. 删除网络配置文件
echo "清理网络配置文件..."
# 删除这些文件可以重置网络偏好设置，重启后系统会自动重建
sudo rm -f /Library/Preferences/SystemConfiguration/com.apple.airport.preferences.plist
sudo rm -f /Library/Preferences/SystemConfiguration/com.apple.wifi.message-tracer.plist
sudo rm -f /Library/Preferences/SystemConfiguration/NetworkInterfaces.plist
sudo rm -f /Library/Preferences/SystemConfiguration/preferences.plist

# 6. 关闭系统代理设置
echo "关闭系统代理设置..."
# 使用更可靠的方法获取服务名称，并过滤掉已禁用的服务（以*开头）
networksetup -listallnetworkservices | tail -n +2 | while IFS= read -r service; do
    # 检查服务是否被禁用（名称前是否有*）
    if [[ "$service" != \** ]]; then
        # 直接使用服务名称，避免不必要的字符串处理
        clean_service="$service"
        echo "  正在关闭代理: $clean_service"
        networksetup -setwebproxystate "$clean_service" off 2>/dev/null
        networksetup -setsecurewebproxystate "$clean_service" off 2>/dev/null
        networksetup -setsocksfirewallproxystate "$clean_service" off 2>/dev/null
        networksetup -setautoproxystate "$clean_service" off 2>/dev/null
    fi
done

echo "网络重置完成！建议重启电脑以使所有更改生效。"

# 询问是否重启
read -p "是否现在重启？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo reboot
fi
