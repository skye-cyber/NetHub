#!/bin/bash

BASE_DIR="/home/skye/captive"
AUTH_FILE="$BASE_DIR/auth/authenticated_macs"

FLASK_PORT="8181"
GATEWAY_IP="192.168.12.1"

echo "Updating firewall rules for authenticated devices..."

# Check if MAC file exists and has content
if [ ! -f "$AUTH_FILE" ]; then
    echo "No authentication file found at $AUTH_FILE"
    exit 1
fi

# Count existing MAC rules for info
existing_macs=$(iptables -L CAPTIVE_PORTAL -n | grep -c "MAC")
echo "Found $existing_macs existing MAC rules in CAPTIVE_PORTAL chain"

# Process each MAC in the auth file
while read -r mac; do
    # Skip empty lines and validate MAC format
    if [ -z "$mac" ]; then
        continue
    fi

    # Clean up MAC address (remove colons/dashes and ensure proper format)
    mac_clean=$(echo "$mac" | tr -d ':-' | sed 's/\(..\)/\1:/g;s/:$//')

    if [[ $mac_clean =~ ^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$ ]]; then
        echo "Processing MAC: $mac_clean"

        # Check if MAC rule already exists in CAPTIVE_PORTAL
        if ! iptables -C CAPTIVE_PORTAL -m mac --mac-source "$mac_clean" -j ACCEPT 2>/dev/null; then
            echo "Adding internet access for MAC: $mac_clean"
            iptables -I CAPTIVE_PORTAL 1 -m mac --mac-source "$mac_clean" -j ACCEPT
        else
            echo "MAC $mac_clean already has access"
        fi

        # Check if MAC rule already exists in AUTH_REDIRECT
        if ! iptables -t nat -C AUTH_REDIRECT -m mac --mac-source "$mac_clean" -j RETURN 2>/dev/null; then
            echo "Adding redirect exemption for MAC: $mac_clean"
            iptables -t nat -I AUTH_REDIRECT 1 -m mac --mac-source "$mac_clean" -j RETURN
        else
            echo "MAC $mac_clean already has redirect exemption"
        fi
    else
        echo "Invalid MAC format: $mac"
    fi
done <"$AUTH_FILE"

echo "Flashing contrac for immediately internet access"

# FLUSH CONNTRACK FOR NEWLY AUTHENTICATED MACs
if [ -f "$AUTH_FILE" ]; then
    while read -r mac; do
        if [ ! -z "$mac" ] && [[ $mac =~ ^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$ ]]; then
            mac_clean=$(echo "$mac" | tr -d ':-' | sed 's/\(..\)/\1:/g;s/:$//')
            echo "Flushing connection tracking for MAC: $mac_clean"
            # Flush all connections for this MAC
            conntrack -D -m "$mac_clean" 2>/dev/null || true
        fi
    done <"$AUTH_FILE"
fi

echo "Firewall rules updated. Authenticated devices can access internet immediately."

# Verify both chains
echo "CAPTIVE_PORTAL chain:"
iptables -L CAPTIVE_PORTAL -n --line-numbers | head -20
echo
echo "AUTH_REDIRECT chain:"
iptables -t nat -L AUTH_REDIRECT -n --line-numbers | head -20
