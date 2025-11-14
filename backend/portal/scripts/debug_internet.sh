#!/bin/bash

BASE_DIR="/home/skye/captive"
AUTH_FILE="$BASE_DIR/auth/authenticated_macs"
CLIENT_IFACE="ap0"
INTERNET_IFACE="eth0"
GATEWAY_IP="192.168.12.1"

echo "=== INTERNET ACCESS DEBUGGING ==="
echo

# Test device (provide as argument or use first authenticated device)
if [ $# -eq 1 ]; then
    TEST_MAC="$1"
else
    TEST_MAC=$(head -1 "$AUTH_FILE" 2>/dev/null)
    if [ -z "$TEST_MAC" ]; then
        echo "No authenticated devices found. Please provide a MAC address:"
        echo "Usage: $0 <MAC-address>"
        exit 1
    fi
    echo "Using first authenticated device: $TEST_MAC"
fi

echo "Debugging internet access for MAC: $TEST_MAC"
echo "=========================================="

# 1. Check if device is connected
echo "1. DEVICE CONNECTION STATUS:"
TEST_IP=$(arp -n -i $CLIENT_IFACE | grep -i "$TEST_MAC" | awk '{print $1}')
if [ -n "$TEST_IP" ]; then
    echo "   ✓ Device connected with IP: $TEST_IP"
else
    echo "   ✗ Device not found in ARP table"
    echo "   Note: Device might need to send traffic first"
    # Try ip neighbor
    TEST_IP=$(ip neigh show dev $CLIENT_IFACE | grep -i "$TEST_MAC" | awk '{print $1}')
    if [ -n "$TEST_IP" ]; then
        echo "   ✓ Device found with IP: $TEST_IP (via ip neigh)"
    else
        echo "   ✗ Device not found. Please make sure device is connected to WiFi"
        exit 1
    fi
fi

echo
echo "2. AUTHENTICATION STATUS:"
if grep -q "$TEST_MAC" "$AUTH_FILE" 2>/dev/null; then
    echo "   ✓ MAC is in authenticated_macs file"
else
    echo "   ✗ MAC NOT found in authenticated_macs file"
    echo "   Run: echo '$TEST_MAC' >> $AUTH_FILE"
    echo "   Then: sudo $BASE_DIR/scripts/update_firewall.sh"
    exit 1
fi

echo
echo "3. FIREWALL RULES:"
echo "   Checking CAPTIVE_PORTAL chain:"
if iptables -L CAPTIVE_PORTAL -n 2>/dev/null | grep -i "$TEST_MAC"; then
    echo "   ✓ Firewall rule found for MAC"
else
    echo "   ✗ No specific firewall rule for MAC"
    echo "   Run: sudo $BASE_DIR/scripts/update_firewall.sh"
fi

echo
echo "   Current CAPTIVE_PORTAL chain:"
iptables -L CAPTIVE_PORTAL -n --line-numbers
echo

echo "4. NAT/FORWARDING RULES:"
echo "   FORWARD chain:"
iptables -L FORWARD -n --line-numbers
echo
echo "   NAT POSTROUTING:"
iptables -t nat -L POSTROUTING -n --line-numbers
echo

echo "5. NETWORK CONFIGURATION:"
echo "   IP forwarding: $(cat /proc/sys/net/ipv4/ip_forward)"
echo "   Gateway IP: $GATEWAY_IP"
echo "   Client interface: $CLIENT_IFACE"
echo "   Internet interface: $INTERNET_IFACE"

echo
echo "6. ROUTING:"
ip route show
echo

echo "7. INTERNET CONNECTION TEST:"
ping -c 2 -W 1 8.8.8.8 >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Gateway has internet access"
else
    echo "   ✗ Gateway has NO internet access"
    echo "   Check your internet connection on $INTERNET_IFACE"
fi

echo
echo "8. REAL-TIME TRAFFIC MONITOR:"
echo "   Monitoring traffic for MAC $TEST_MAC for 10 seconds..."
echo "   Generate some traffic from the device (try browsing)..."
echo
tcpdump -i $CLIENT_IFACE -c 10 ether host $TEST_MAC 2>/dev/null || echo "   tcpdump not available"

echo
echo "9. MANUAL PACKET TEST:"
if [ -n "$TEST_IP" ]; then
    echo "   Testing from gateway perspective:"
    # Simulate traffic from device
    echo "   Try this on the device: ping 8.8.8.8"
    echo "   Or: curl -v http://example.com"

    # Check if we see the traffic
    echo
    echo "   Current connections from $TEST_IP:"
    netstat -tn 2>/dev/null | grep $TEST_IP || echo "   No active connections"
fi

echo
echo "=========================================="
echo "NEXT STEPS:"
echo "1. Make sure device is connected to WiFi"
echo "2. Run: sudo $BASE_DIR/scripts/update_firewall.sh"
echo "3. Try browsing from device"
echo "4. Check if traffic appears in tcpdump"
echo "=========================================="
