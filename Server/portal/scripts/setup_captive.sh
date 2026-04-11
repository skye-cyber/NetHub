#!/bin/bash

# Interface facing the clients (your hotspot interface)
CLIENT_IFACE="ap0"

# Interface facing the internet
INTERNET_IFACE="eth0"

BASE_DIR="/home/skye/captive"

# Gateway IP for the captive portal
GATEWAY_IP="192.168.12.1"
SUBNET="192.168.12.0/24"

# Flask server port
FLASK_PORT="8181"

# Directory for tracking authenticated MACs
AUTH_DIR="$BASE_DIR/auth"
MAC_AUTH_FILE="$AUTH_DIR/authenticated_macs"

# Create directory structure
mkdir -p $AUTH_DIR
touch $MAC_AUTH_FILE
chmod 666 $MAC_AUTH_FILE

# Enable IP forwarding
echo 1 >/proc/sys/net/ipv4/ip_forward

# Clear existing rules
iptables -F
iptables -t nat -F
iptables -X
iptables -t nat -X

# Default policies
iptables -P INPUT ACCEPT
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# ===== CREATE CHAINS =====
echo "Creating chains"

# Create captive portal chain or flush if exists
iptables -N CAPTIVE_PORTAL 2>/dev/null || iptables -F CAPTIVE_PORTAL
iptables -t nat -N AUTH_REDIRECT 2>/dev/null || iptables -t nat -F AUTH_REDIRECT

# ===== BASIC FORWARDING RULES =====
echo "Setting basic forwarding rules"

# Allow established connections (IMPORTANT: must come first)
iptables -A FORWARD -i $INTERNET_IFACE -o $CLIENT_IFACE -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow access to gateway (captive portal)
iptables -A FORWARD -i $CLIENT_IFACE -d $GATEWAY_IP -j ACCEPT

# Allow DNS queries
iptables -A FORWARD -i $CLIENT_IFACE -o $INTERNET_IFACE -p udp --dport 53 -j ACCEPT

# ===== NAT REDIRECT RULES =====
echo "Setting NAT redirect rules"

# Clear NAT rules
iptables -t nat -F PREROUTING

# Send HTTP/HTTPS traffic to AUTH_REDIRECT chain for processing
iptables -t nat -A PREROUTING -i $CLIENT_IFACE -p tcp --dport 80 -j AUTH_REDIRECT
iptables -t nat -A PREROUTING -i $CLIENT_IFACE -p tcp --dport 443 -j AUTH_REDIRECT

# Setup AUTH_REDIRECT chain:
# 1. First, authenticated MACs will RETURN (bypass redirect) - added by update script
# 2. Then, redirect all others to captive portal
iptables -t nat -A AUTH_REDIRECT -p tcp --dport 80 -j REDIRECT --to-port $FLASK_PORT
iptables -t nat -A AUTH_REDIRECT -p tcp --dport 443 -j REDIRECT --to-port $FLASK_PORT

# Redirect DNS queries to ourselves
iptables -t nat -A PREROUTING -i $CLIENT_IFACE -p udp --dport 53 -j REDIRECT --to-port 53

# ===== CAPTIVE PORTAL CHAIN RULES =====
echo "Setting captive portal chain rules"

# Main forwarding chain - send all client traffic to captive portal chain
iptables -A FORWARD -i $CLIENT_IFACE -o $INTERNET_IFACE -j CAPTIVE_PORTAL

# 1. First position: authenticated MACs (will be inserted here by update script)
#    This is intentionally left empty - update script will insert rules here

# 2. Allow traffic to gateway (CRITICAL - allows redirected traffic to reach Flask)
iptables -A CAPTIVE_PORTAL -d $GATEWAY_IP -j ACCEPT

# 3. Allow essential services
iptables -A CAPTIVE_PORTAL -p udp --dport 53 -j ACCEPT    # DNS
iptables -A CAPTIVE_PORTAL -p udp --dport 67:68 -j ACCEPT # DHCP

# 4. Allow HTTP/HTTPS traffic (it will be redirected by NAT rules above)
iptables -A CAPTIVE_PORTAL -p tcp --dport 80 -j ACCEPT
iptables -A CAPTIVE_PORTAL -p tcp --dport 443 -j ACCEPT

# 5. Log new connections (optional)
iptables -A CAPTIVE_PORTAL -m conntrack --ctstate NEW -j LOG --log-prefix "CAPTIVE_NEW: "

# 6. Drop all other traffic from unauthenticated devices
iptables -A CAPTIVE_PORTAL -j DROP

# ===== NAT MASQUERADE =====
echo "Setting NAT masquerade"

# NAT for internet access
iptables -t nat -A POSTROUTING -o $INTERNET_IFACE -j MASQUERADE

# ===== INPUT RULES =====
echo "Setting input rules"

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow HTTP to captive portal
iptables -A INPUT -p tcp --dport $FLASK_PORT -j ACCEPT

# Logging (optional)
iptables -A INPUT -p tcp --dport $FLASK_PORT -j LOG --log-prefix "CAPTIVE_PORTAL: "

echo "Captive portal setup complete"
echo "Gateway IP: $GATEWAY_IP"
echo "Flask port: $FLASK_PORT"
echo "HTTP/HTTPS traffic will be redirected to captive portal"

# Initialize with any existing authenticated MACs
if [ -f "$MAC_AUTH_FILE" ] && [ -s "$MAC_AUTH_FILE" ]; then
    echo "Initializing with existing authenticated MACs..."
    $BASE_DIR/scripts/update_firewall.sh
fi
