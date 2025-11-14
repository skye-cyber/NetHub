#!/bin/bash
echo "=== Testing Your Captive Portal Setup ==="

echo "1. Network interfaces:"
ip addr show ap0
echo

echo "2. iptables rules:"
echo "   NAT PREROUTING:"
iptables -t nat -L PREROUTING -n --line-numbers
echo
echo "   FORWARD chain:"
iptables -L FORWARD -n --line-numbers
echo
echo "   CAPTIVE_PORTAL chain:"
iptables -L CAPTIVE_PORTAL -n --line-numbers
echo

echo "3. Services:"
echo "   Dnsmasq: $(pgrep dnsmasq && echo 'RUNNING' || echo 'STOPPED')"
echo "   Flask: $(pgrep -f 'python.*8181' && echo 'RUNNING' || echo 'STOPPED')"
echo

echo "4. Test from client:"
echo "   Connect to WiFi and try:"
echo "   curl -v http://example.com"
echo "   curl -v http://192.168.12.1:8181"
echo "   Should both show your captive portal"
