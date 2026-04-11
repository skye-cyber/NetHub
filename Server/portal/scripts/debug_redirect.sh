#!/bin/bash

echo "=== DEBUGGING IPTABLES REDIRECT ==="
echo

echo "1. Current NAT PREROUTING rules:"
sudo iptables -t nat -L PREROUTING -n --line-numbers -v
echo

echo "2. Current FORWARD chain:"
sudo iptables -L FORWARD -n --line-numbers -v
echo

echo "3. Testing from client perspective:"
echo "   Simulating client request through iptables..."
echo

# Create a test packet and see if it gets redirected
echo "4. Checking if packets are hitting the rules:"
echo "   Clear counters first..."
sudo iptables -t nat -Z
sudo iptables -Z

echo "   Now generate traffic from a connected device..."
echo "   Or run this from another device: curl -v http://example.com"
read -p "   Press Enter after generating traffic..."

echo
echo "5. Packet counters:"
echo "   NAT PREROUTING:"
sudo iptables -t nat -L PREROUTING -n -v --line-numbers
echo
echo "   FORWARD chain:"
sudo iptables -L FORWARD -n -v --line-numbers
echo

echo "6. Interface status:"
ip addr show ap0
echo
echo "   Routing table:"
ip route show
