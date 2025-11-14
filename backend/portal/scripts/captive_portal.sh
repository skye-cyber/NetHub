#!/bin/bash

CAPTIVE_DIR="/home/skye/captive"
FLASK_APP="$CAPTIVE_DIR/app.py"
LOG_FILE="$CAPTIVE_DIR/logs/captive_setup.log"

C_WBOLD="\033[1m"
C_YELLOW="\033[0m"
C_BLUE="\033[94m"
C_GREEN="\033[32m"
C_RED='\033[31m'
C_RESET="\033[0m"

case "$1" in
start)
    echo "Starting captive portal..."

    # Stop existing services
    service dnsmasq stop
    pkill -f "captive/app.py"

    # Configure network interface
    ifconfig ap0 192.168.12.1 netmask 255.255.255.0 broadcast 192.168.12.255 up
    # Configure dnsmasq to bind only to my hotspot interface
    echo "\
# Listening interface
interface=ap0
bind-interfaces
listen-address=192.168.12.1

# DHCP range
dhcp-range=192.168.12.10,192.168.12.100,255.255.255.0,12h

# Gateway
dhcp-option=3,192.168.12.1

dhcp-option=6,8.8.8.8,1.1.1.1  # ALWAYS give real DNS

# Authenticated devices get real DNS
dhcp-option=tag:authenticated,6,8.8.8.8,1.1.1.1

# Unauthenticated devices get gateway DNS (redirects to captive portal)
dhcp-option=tag:!authenticated,6,192.168.12.1

# Always return our IP for all domains (captive portal effect)
# address=/#/192.168.12.1

# DNS forwarders (for authenticated devices)
server=8.8.8.8
server=1.1.1.1

# Logging
log-dhcp
log-queries

log-facility=$CAPTIVE_DIR/logs/dnsmasq.log

# Force DHCP offers even if no dhcprequest
dhcp-authoritative
dhcp-leasefile=/var/lib/misc/dnsmasq.leases

# Rapid commit support
dhcp-rapid-commit\
    " >/etc/dnsmasq.d/portal.conf

    # Stop Apache
    sudo systemctl stop apache2
    #sudo systemctl disable apache2

    # Kill any process using port 80
    # sudo fuser -k 80/tcp 2>/dev/null

    # Start services
    $CAPTIVE_DIR/scripts/setup_captive.sh
    # sudo systemctl start dnsmasq
    # sudo kill 1576 1677
    # sudo ss -lun | grep :67 || echo "port 67 free"
    # Find how dnsmasq was launched
    # journalctl -u dnsmasq --since "5 minutes ago"
    sudo pkill dnsmasq
    sudo dnsmasq -C /etc/dnsmasq.d/portal.conf

    # Start Flask app in background
    cd $CAPTIVE_DIR
    nohup python3 $FLASK_APP >$LOG_FILE 2>&1 &

    # pkill -f "waitress-serve"

    # Start waitress binding to all interfaces
    # nohup waitress-serve --host=0.0.0.0 --port=8181 app:app >logs/waitress.log 2>&1 &

    # Start device detection
    while true; do
        $CAPTIVE_DIR/scripts/detect_devices.sh
        sleep 30
    done &

    echo -e "$C_WBOLD- Captive portal started with Flask $C_RESET"

    echo "1. Test configuration configuration..."
    sudo dnsmasq --test -C /etc/dnsmasq.d/portal.conf && echo "✓ Config valid" || echo "✗ Config invalid"

    echo "2. Testing DNS redirect..."
    echo "   From gateway:"
    nslookup google.com 192.168.12.1
    # echo
    # echo "   Should return: 192.168.12.1 for ALL domains"

    # echo "3. dnsmasq status:"
    # sudo netstat -tlnp | grep :53
    # echo

    ;;

stop)
    echo "Stopping captive portal..."
    pkill -f "captive/app.py"
    pkill -f "detect_devices.sh"
    service dnsmasq stop

    # Clear iptables rules
    iptables -F
    iptables -t nat -F
    iptables -X
    iptables -t nat -X

    echo "Captive portal stopped"
    ;;

status)
    echo "Flask app status:"
    pgrep -f "captive/app.py" >/dev/null && echo -e "$C_GREEN Running $C_RESET" || echo -e "$C_RED Stopped $C_RESET"

    echo -e "\nAuthenticated devices:"
    cat $CAPTIVE_DIR/auth/authenticated_macs 2>/dev/null || echo -e "$C_YELLOW No authenticated devices $C_RESET"

    echo -e "\nCurrent ARP entries:"
    arp -n | grep ap0
    ;;

monitor)
    #chmod +x "$CAPTIVE_DIR/scripts/monitor_devices.sh"
    "$CAPTIVE_DIR/scripts/monitor_devices.sh"
    ;;
check)
    # chmod +x "$CAPTIVE_DIR/scripts/check_access.sh"
    "$CAPTIVE_DIR/scripts/check_access.sh" $2
    ;;
test)
    echo -e "$C_WBOLD-Performing Tests$C_RESET"
    # chmod +x "$CAPTIVE_DIR/scripts/integrity_test.sh"
    "$CAPTIVE_DIR/scripts/integrity_test.sh"
    ;;
debug)
    # chmod +x "$CAPTIVE_DIR/scripts/debug_internet.sh"
    "$CAPTIVE_DIR/scripts/debug_internet.sh"
    ;;
firewall-rules)
    # chmod +x "$CAPTIVE_DIR/scripts/firewall_rules.sh"
    "$CAPTIVE_DIR/scripts/firewall_rules.sh"
    ;;
reset)
    chmod +x "$CAPTIVE_DIR/scripts/clean_reset.sh"
    "$CAPTIVE_DIR/scripts/clean_reset.sh"
    ;;

*)
    echo "Usage: $0 {start|stop|status|test|monitor|check|firewall-rules|reset}"
    exit 1
    ;;
esac
