#!/bin/bash

# Configuration
SUBNET="192.168.12.0/24"
BASE_DIR="/home/skye/captive"
AUTH_DIR="$BASE_DIR/auth"
AUTH_FILE="$AUTH_DIR/authenticated_macs"
LOG_DIR="$BASE_DIR/logs/"
LOG_FILE="$LOG_DIR/device_detection.log"
INTERFACE="ap0"

# Create directories if they don't exist
mkdir -p "$AUTH_DIR" "$LOG_DIR"
touch "$AUTH_FILE" "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >>"$LOG_FILE"
}

# Function to get MAC address from IP (more reliable method)
get_mac_from_ip() {
    local ip="$1"
    # Try multiple methods to get MAC address
    mac=$(arp -n "$ip" 2>/dev/null | awk '/'"$ip"'/ {print $3}')

    # If arp fails, try ip neigh
    if [[ ! "$mac" =~ ..:..:..:..:..:.. ]]; then
        mac=$(ip neigh show dev "$INTERFACE" | grep "^$ip " | awk '{print $5}')
    fi

    # Validate MAC format
    if [[ "$mac" =~ ^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$ ]]; then
        echo "$mac" | tr '[:upper:]' '[:lower:]'
    else
        echo ""
    fi
}

log_message "Starting device detection scan on interface $INTERFACE"

# Get list of IPs in the subnet using multiple methods
IP_LIST=$(nmap -sn "$SUBNET" 2>/dev/null | grep 'Nmap scan report' | awk '{print $NF}' | tr -d '()')

# If nmap fails, use ping sweep
if [ -z "$IP_LIST" ]; then
    IP_LIST=$(for i in {1..254}; do ping -c 1 -W 1 "192.168.12.$i" 2>/dev/null | grep "from" | awk '{print $4}' | cut -d: -f1; done)
fi

# Process each IP
for ip in $IP_LIST; do
    # Skip gateway IP
    if [ "$ip" = "192.168.12.1" ]; then
        continue
    fi

    mac=$(get_mac_from_ip "$ip")

    if [ -n "$mac" ]; then
        # Check if MAC is already authenticated
        if ! grep -qi "$mac" "$AUTH_FILE" 2>/dev/null; then
            log_message "NEW DEVICE DETECTED - IP: $ip, MAC: $mac"

            # Optional: Log device details for analysis
            echo "$(date '+%Y-%m-%d %H:%M:%S'),$ip,$mac,new" >>"$AUTH_DIR/device_history.csv"

            # Automatic actions would go here:
            # - Send notification
            # - Trigger specific welcome page
            # - Apply temporary restrictions
        else
            # Device is authenticated, log activity occasionally
            if [ $((RANDOM % 10)) -eq 0 ]; then # Log ~10% of authenticated device sightings
                log_message "Authenticated device active - IP: $ip, MAC: $mac"
            fi
        fi
    fi
done

# Additional: Check for stale ARP entries and clean up
log_message "Device detection scan completed. $(echo "$IP_LIST" | wc -w) devices found."

# Optional: Clean up old log entries (keep last 1000 lines)
tail -n 1000 "$LOG_FILE" >"$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
