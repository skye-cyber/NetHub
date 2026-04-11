#!/bin/bash

BASE_DIR="/home/skye/captive"
AUTH_FILE="$BASE_DIR/auth/authenticated_macs"
INTERFACE="ap0"

echo "=== REAL-TIME DEVICE MONITOR ==="
echo "Press Ctrl+C to stop monitoring"
echo

while true; do
    clear
    echo "$(date): Scanning network..."
    echo

    # Get all connected devices
    echo "CONNECTED DEVICES:"
    echo "IP Address       MAC Address         Status       Hostname"
    echo "------------------------------------------------------------"

    # Method 1: arp table
    arp -n -i $INTERFACE | grep "192.168.12." | while read line; do
        IP=$(echo $line | awk '{print $1}')
        MAC=$(echo $line | awk '{print $3}' | tr '[:upper:]' '[:lower:]')

        if [ -n "$MAC" ] && [[ $MAC =~ ^([0-9a-f]{2}[:-]){5}([0-9a-f]{2})$ ]]; then
            # Check authentication status
            if grep -q "$MAC" "$AUTH_FILE" 2>/dev/null; then
                STATUS="AUTHENTICATED"
            else
                STATUS="BLOCKED"
            fi

            # Try to get hostname
            HOSTNAME=$(nslookup "$IP" 2>/dev/null | grep "name =" | awk '{print $4}' | sed 's/\.$//')
            if [ -z "$HOSTNAME" ]; then
                HOSTNAME="unknown"
            fi

            printf "%-16s %-18s %-12s %s\n" "$IP" "$MAC" "$STATUS" "$HOSTNAME"
        fi
    done

    echo
    echo "Summary:"
    TOTAL_DEVICES=$(arp -n -i $INTERFACE | grep "192.168.12." | wc -l)
    AUTH_DEVICES=$(arp -n -i $INTERFACE | grep "192.168.12." | while read line; do
        MAC=$(echo $line | awk '{print $3}' | tr '[:upper:]' '[:lower:]')
        if grep -q "$MAC" "$AUTH_FILE" 2>/dev/null; then echo "1"; fi
    done | wc -l)

    echo "Total devices: $TOTAL_DEVICES"
    echo "Authenticated: $AUTH_DEVICES"
    echo "Blocked: $((TOTAL_DEVICES - AUTH_DEVICES))"

    echo
    echo "Refreshing in 10 seconds..."
    sleep 10
done
