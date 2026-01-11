#!/bin/bash

# Comprehensive installation and testing script for NetHub Hotspot Manager

echo "=== NetHub Hotspot Manager Installation and Test Script ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install dependencies
default_install_dependencies() {
    echo -e "${YELLOW}Installing required dependencies...${NC}"
    
    if command_exists apt; then
        # Debian/Ubuntu
        apt update
        apt install -y network-manager hostapd dnsmasq iptables python3 python3-pip
    elif command_exists dnf; then
        # Fedora
        dnf install -y NetworkManager hostapd dnsmasq iptables python3 python3-pip
    elif command_exists pacman; then
        # Arch
        pacman -S --noconfirm networkmanager hostapd dnsmasq iptables python python-pip
    else
        echo -e "${RED}Error: Unsupported package manager${NC}"
        return 1
    fi
    
    # Install Python dependencies
    pip3 install -r requirements.txt || true
    
    echo -e "${GREEN}Dependencies installed successfully${NC}"
}

# Function to setup sudo permissions
setup_sudo_permissions() {
    echo -e "${YELLOW}Setting up sudo permissions...${NC}"
    
    # Create sudoers file for ap_manager
    cat > /etc/sudoers.d/ap_manager << EOF
# Allow ap_manager to run network commands without password
ALL ALL=NOPASSWD: /usr/local/bin/ap_manager
ALL ALL=NOPASSWD: /usr/bin/ip
ALL ALL=NOPASSWD: /usr/bin/iptables
ALL ALL=NOPASSWD: /usr/bin/iw
ALL ALL=NOPASSWD: /usr/bin/modprobe
ALL ALL=NOPASSWD: /usr/bin/systemctl
ALL ALL=NOPASSWD: /usr/bin/nmcli
ALL ALL=NOPASSWD: /usr/bin/dnsmasq
ALL ALL=NOPASSWD: /usr/bin/hostapd
EOF
    
    # Set proper permissions
    chmod 440 /etc/sudoers.d/ap_manager
    
    echo -e "${GREEN}Sudo permissions configured successfully${NC}"
}

# Function to install the hotspot manager
install_hotspot_manager() {
    echo -e "${YELLOW}Installing hotspot manager...${NC}"
    
    # Create installation directory
    INSTALL_DIR="/opt/ap_manager"
    BASE_DIR="/etc/ap_manager"
    
    mkdir -p "$INSTALL_DIR/"
    mkdir -p "$BASE_DIR/conf"
    mkdir -p "$BASE_DIR/proc"
    
    # Copy files
    cp -r backend/hotspotmanager/ap_utils "$INSTALL_DIR/"
    cp backend/hotspotmanager/*.sh "$INSTALL_DIR/"
    cp backend/hotspotmanager/*.py "$INSTALL_DIR/"
    cp -r backend/hotspotmanager/config/* "$BASE_DIR/conf/"
    mv "$BASE_DIR/conf/config-bc.json" "$BASE_DIR/.config-bc.json"
    
    # Set proper permissions
    chmod 755 "$BASE_DIR" -R
    chmod +x "$INSTALL_DIR"/*.sh
    chmod +x "$INSTALL_DIR"/*.py
    
    # Create symlink in /usr/local/bin for easy access
    ln -sf "$INSTALL_DIR/ap_cli.py" /usr/local/bin/ap_manager
    
    echo -e "${GREEN}Hotspot manager installed successfully${NC}"
}

# Function to test the installation
test_installation() {
    echo -e "${YELLOW}Testing installation...${NC}"
    
    # Test sudo permissions
    echo -e "${BLUE}Testing sudo permissions...${NC}"
    if sudo -n whoami | grep -q "^root$"; then
        echo -e "${GREEN}Sudo permissions working correctly${NC}"
    else
        echo -e "${RED}Warning: Sudo permissions may not be working correctly${NC}"
    fi
    
    # Test if ap_manager is accessible
    echo -e "${BLUE}Testing ap_manager accessibility...${NC}"
    if [[ -f "/usr/local/bin/ap_manager" ]]; then
        echo -e "${GREEN}ap_manager is accessible${NC}"
    else
        echo -e "${RED}Error: ap_manager not found in /usr/local/bin/${NC}"
        return 1
    fi
    
    # Test basic functionality
    echo -e "${BLUE}Testing basic functionality...${NC}"
    
    # Test if we can run the Python script
    if python3 -c "import sys; sys.path.insert(0, '/opt/ap_manager'); from ap_manager import ApManager; print('ApManager imported successfully')" 2>/dev/null; then
        echo -e "${GREEN}Basic functionality test passed${NC}"
    else
        echo -e "${RED}Warning: Basic functionality test failed${NC}"
    fi
    
    echo -e "${GREEN}Installation test completed${NC}"
}

# Function to show usage information
show_usage() {
    echo -e "${BLUE}NetHub Hotspot Manager Usage${NC}"
    echo ""
    echo "After installation, you can use the following commands:"
    echo ""
    echo "  ap_manager start          # Start hotspot"
    echo "  ap_manager stop           # Stop hotspot"
    echo "  ap_manager status         # Check status"
    echo "  ap_manager configure      # Configure hotspot settings"
    echo "  ap_manager interfaces     # Show available wireless interfaces"
    echo ""
    echo "Example usage:"
    echo "  ap_manager configure --ssid MyHotspot --password MyPass123 --interface wlan0"
    echo "  ap_manager start"
    echo ""
    echo "For automatic startup:"
    echo "  systemctl enable ap_manager.service"
    echo "  systemctl start ap_manager.service"
}

# Main installation process
main() {
    echo -e "${YELLOW}Starting installation process...${NC}"
    
    # Install dependencies
    if ! default_install_dependencies; then
        echo -e "${RED}Dependency installation failed${NC}"
        exit 1
    fi
    
    # Setup sudo permissions
    if ! setup_sudo_permissions; then
        echo -e "${RED}Sudo permission setup failed${NC}"
        exit 1
    fi
    
    # Install hotspot manager
    if ! install_hotspot_manager; then
        echo -e "${RED}Hotspot manager installation failed${NC}"
        exit 1
    fi
    
    # Test installation
    if ! test_installation; then
        echo -e "${RED}Installation test failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}"
    echo "=== Installation completed successfully! ==="
    echo -e "${NC}"
    
    show_usage
    
    echo -e "${YELLOW}"
    echo "You can now create hotspots using the ap_manager command."
    echo "Example: ap_manager start"
    echo -e "${NC}"
}

# Run main function
main
