SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/ap_cli.py"
echo $PYTHON_SCRIPT
# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Install dependencies
install_dependencies() {
    echo -e "${YELLOW}Installing dependencies...${NC}"

    if command -v apt &> /dev/null; then
        # Debian/Ubuntu
        # apt update
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

install_dependencies
