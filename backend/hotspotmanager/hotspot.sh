#!/bin/bash

# Custom Hotspot Manager - Bash Wrapper
# Provides a user-friendly interface for the Python hotspot manager

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/hotspot_manager.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}Error: This script must be run as root${NC}"
        exit 1
    fi
}

# Check if Python script exists
check_python_script() {
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        echo -e "${RED}Error: Python script not found at $PYTHON_SCRIPT${NC}"
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    echo -e "${YELLOW}Installing dependencies...${NC}"

    if command -v apt &> /dev/null; then
        # Debian/Ubuntu
        apt update
        apt install -y network-manager hostapd dnsmasq iptables python3
    elif command -v dnf &> /dev/null; then
        # Fedora
        dnf install -y NetworkManager hostapd dnsmasq iptables python3
    elif command -v pacman &> /dev/null; then
        # Arch
        pacman -S --noconfirm networkmanager hostapd dnsmasq iptables python
    else
        echo -e "${RED}Unsupported package manager${NC}"
        return 1
    fi

    echo -e "${GREEN}Dependencies installed successfully${NC}"
}

# Show usage
show_usage() {
    echo -e "${BLUE}Custom Hotspot Manager${NC}"
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  start       - Start the hotspot"
    echo "  stop        - Stop the hotspot"
    echo "  status      - Show hotspot status"
    echo "  configure   - Configure hotspot settings"
    echo "  interfaces  - Show available wireless interfaces"
    echo "  install     - Install dependencies"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 configure --ssid MyHotspot --password MyPass123"
    echo "  $0 status"
}

# Interactive configuration
interactive_configure() {
    echo -e "${YELLOW}Interactive Hotspot Configuration${NC}"

    read -p "Enter SSID [MyCustomHotspot]: " ssid
    ssid=${ssid:-MyCustomHotspot}

    read -sp "Enter Password [StrongPassword123]: " password
    password=${password:-StrongPassword123}
    echo

    read -p "Enter Interface [wlan0]: " interface
    interface=${interface:-wlan0}

    echo "Select mode:"
    echo "1) NetworkManager (nmcli) - Recommended for desktop"
    echo "2) systemd-networkd - Advanced users"
    read -p "Choose [1]: " mode_choice

    case $mode_choice in
        2) mode="systemd" ;;
        *) mode="nmcli" ;;
    esac

    python3 "$PYTHON_SCRIPT" configure --ssid "$ssid" --password "$password" --interface "$interface" --mode "$mode"
}

case "$1" in
    start)
        check_root
        check_python_script
        python3 "$PYTHON_SCRIPT" start
        ;;
    stop)
        check_root
        check_python_script
        python3 "$PYTHON_SCRIPT" stop
        ;;
    status)
        check_python_script
        python3 "$PYTHON_SCRIPT" status
        ;;
    configure)
        check_root
        check_python_script
        if [[ $# -eq 1 ]]; then
            interactive_configure
        else
            shift
            python3 "$PYTHON_SCRIPT" configure "$@"
        fi
        ;;
    interfaces)
        check_python_script
        python3 "$PYTHON_SCRIPT" interfaces
        ;;
    install)
        check_root
        install_dependencies
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
