#!/bin/bash

CAPTIVE_DIR="/home/skye/captive"

echo "=== COMPLETE CAPTIVE PORTAL RESET ==="
echo

# Stop everything
echo "1. Stopping all services..."
# sudo pkill -f "flask"
sudo pkill -f "python.*app.py"
sudo pkill -f "detect_devices.sh"
sudo service dnsmasq stop 2>/dev/null
sudo killall dnsmasq 2>/dev/null

# Clear all iptables rules
echo "2. Clearing all iptables rules..."
sudo iptables -F
sudo iptables -t nat -F
sudo iptables -X
sudo iptables -t nat -X

# Reset to default policies
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT

# Clear authenticated devices
echo "3. Clearing authenticated devices..."
AUTH_FILE="$CAPTIVE_DIR/auth/authenticated_macs"
if [ -f "$AUTH_FILE" ]; then
    sudo cp "$AUTH_FILE" "$AUTH_FILE.backup"
    sudo truncate -s 0 "$AUTH_FILE"
    echo "   Backup created: $AUTH_FILE.backup"
    echo "   Authenticated devices cleared"
else
    sudo touch "$AUTH_FILE"
fi

# Clear ARP cache for ap0
echo "4. Clearing ARP cache..."
sudo ip neigh flush dev ap0 2>/dev/null

# Restart network interface
echo "5. Restarting network interface..."
sudo ip link set ap0 down
sudo ip link set ap0 up
sudo ip addr flush dev ap0
sudo ip addr add 192.168.12.1/24 dev ap0

# Kill any processes using port 8181
echo "6. Freeing up port 8181..."
sudo fuser -k 8181/tcp 2>/dev/null

# Clear logs
echo "7. Clearing logs..."
LOG_FILES="/var/log/captive/* $CAPTIVE_DIR/logs/* $CAPTIVE_DIR/logs/dnsmasq.log"
for log in $LOG_FILES; do
    if [ -f "$log" ]; then
        sudo truncate -s 0 "$log"
        echo "   Cleared: $log"
    fi
done

echo
echo "=== RESET COMPLETE ==="
echo "All services stopped, rules cleared, and devices reset."
echo "Ready for fresh start."
