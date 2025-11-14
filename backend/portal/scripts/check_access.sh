#!/bin/bash

BASE_DIR="/home/skye/captive"
AUTH_FILE="$BASE_DIR/auth/authenticated_macs"
LOG_FILE="$BASE_DIR/logs/device_detection.log"

echo "=== CAPTIVE PORTAL ACCESS VERIFICATION ==="
echo

# Check if MAC or IP provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <MAC-address|IP-address>"
    echo "Example: $0 aa:bb:cc:dd:ee:ff"
    echo "Example: $0 192.168.12.105"
    exit 1
fi

INPUT=$1

# Determine if input is MAC or IP
if [[ $INPUT =~ ^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$ ]]; then
    echo "Checking MAC address: $INPUT"
    MAC=$(echo "$INPUT" | tr '[:upper:]' '[:lower:]')
    IP=""
elif [[ $INPUT =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Checking IP address: $INPUT"
    IP="$INPUT"
    # Get MAC from IP
    MAC=$(arp -n "$IP" 2>/dev/null | awk '/'"$IP"'/ {print $3}' | tr '[:upper:]' '[:lower:]')
    if [ -z "$MAC" ]; then
        MAC=$(ip neigh show dev ap0 | grep "^$IP " | awk '{print $5}' | tr '[:upper:]' '[:lower:]')
    fi
else
    echo "Error: Invalid format. Please provide MAC (aa:bb:cc:dd:ee:ff) or IP (192.168.12.xxx)"
    exit 1
fi

echo "----------------------------------------"

# Check authentication status
if [ -n "$MAC" ]; then
    echo "✓ MAC Address: $MAC"

    if grep -q "$MAC" "$AUTH_FILE" 2>/dev/null; then
        echo "✓ AUTHENTICATION: GRANTED (Device has internet access)"
        AUTH_STATUS="GRANTED"
    else
        echo "✗ AUTHENTICATION: BLOCKED (Device redirected to captive portal)"
        AUTH_STATUS="BLOCKED"
    fi
else
    echo "✗ Could not find MAC address for IP: $IP"
    echo "  Device might not be connected or ARP entry expired"
fi

echo "----------------------------------------"

# Check current connection status
if [ -n "$IP" ]; then
    echo "Current connection status:"
    # Check if device is in ARP table
    if arp -n "$IP" 2>/dev/null | grep -q "$IP"; then
        echo "  ✓ Device is currently connected"
        CONNECTION_STATUS="CONNECTED"
    else
        # Try ip neighbor
        if ip neigh show dev ap0 | grep -q "^$IP "; then
            echo "  ✓ Device is currently connected"
            CONNECTION_STATUS="CONNECTED"
        else
            echo "  ✗ Device not found in network tables"
            echo "  Note: Device might be connected but no recent traffic"
            CONNECTION_STATUS="DISCONNECTED"
        fi
    fi
fi

echo "----------------------------------------"

# Check firewall rules
echo "Firewall status:"
if iptables -L CAPTIVE_PORTAL -n 2>/dev/null | grep -q "$MAC"; then
    echo "  ✓ Firewall rule found for MAC"
else
    echo "  ✗ No specific firewall rule for MAC (using default rules)"
fi

echo "----------------------------------------"

# Show recent activity
if [ -f "$LOG_FILE" ]; then
    echo "Recent activity for this device:"
    grep -i "$MAC" "$LOG_FILE" | tail -5 || echo "  No recent activity found in logs"
fi

echo "========================================"
