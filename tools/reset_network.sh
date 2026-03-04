#!/bin/bash

echo "开始重置 macOS 网络设置..."

# 1. 刷新 DNS
echo "刷新 DNS 缓存..."
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# 2. 重启网络接口
iface="$(route get default 2>/dev/null | awk '/interface:/{print $2; exit}')"
if [ -z "$iface" ]; then
    iface="en0"
fi
echo "重启网络接口: $iface"
sudo ifconfig "$iface" down
sleep 2
sudo ifconfig "$iface" up

# 3. 释放 DHCP
echo "释放 DHCP 租约..."
sudo ipconfig set "$iface" BOOTP
sleep 2
sudo ipconfig set "$iface" DHCP

# 4. 删除网络缓存
echo "清理网络缓存..."
sudo rm -f /Library/Preferences/SystemConfiguration/com.apple.airport.preferences.plist
sudo rm -f /Library/Preferences/SystemConfiguration/com.apple.wifi.message-tracer.plist

# 5. 重启网络服务
echo "重启网络服务..."
sudo launchctl unload /System/Library/LaunchDaemons/com.apple.networking.plist
sudo launchctl load /System/Library/LaunchDaemons/com.apple.networking.plist

echo "关闭系统代理设置..."
networksetup -listallnetworkservices | tail -n +2 | while read -r service; do
    clean_service="${service#* }"
    if [ -n "$clean_service" ]; then
        networksetup -setwebproxystate "$clean_service" off
        networksetup -setsecurewebproxystate "$clean_service" off
        networksetup -setsocksfirewallproxystate "$clean_service" off
        networksetup -setautoproxystate "$clean_service" off
        networksetup -setautoproxyurl "$clean_service" ""
    fi
done

echo "网络重置完成！建议重启电脑。"

# 询问是否重启
read -p "是否现在重启？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo reboot
fi
