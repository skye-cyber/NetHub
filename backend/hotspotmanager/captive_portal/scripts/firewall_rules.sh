#!/bin/bash
echo "=== CURRENT FIREWALL STATE ==="
echo

echo "1. CAPTIVE_PORTAL chain:"
iptables -L CAPTIVE_PORTAL -n --line-numbers -v
echo

echo "2. FORWARD chain:"
iptables -L FORWARD -n --line-numbers -v
echo

echo "3. NAT PREROUTING:"
iptables -t nat -L PREROUTING -n --line-numbers -v
echo

echo "4. NAT POSTROUTING:"
iptables -t nat -L POSTROUTING -n --line-numbers -v
echo

echo "5. All chains containing 'CAPTIVE':"
iptables -L | grep -i captive
iptables -t nat -L | grep -i captive
