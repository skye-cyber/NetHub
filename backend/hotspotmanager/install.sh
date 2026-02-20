#!/bin/bash

# Installation script for AP Manager

set -e
# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "Installing ap_manager Manager..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Create installation directory
INSTALL_DIR="/opt/ap_manager"
BASE_DIR="/etc/ap_manager"

mkdir -p "$INSTALL_DIR/"
mkdir -p "$BASE_DIR/conf"
mkdir -p "$BASE_DIR/proc"

# Copy files
cp -r commsys "$INSTALL_DIR/"
cp -r cli "$INSTALL_DIR/"
cp -r captive_portal "$INSTALL_DIR/"
cp -r ap_utils "$INSTALL_DIR/"
cp -r core "$INSTALL_DIR/"
cp *.sh "$INSTALL_DIR/"
cp *.py "$INSTALL_DIR/"
cp -r config/* "$BASE_DIR/conf/"
mv "$BASE_DIR/conf/config-bc.json" "$BASE_DIR/.config-bc.json"

# Set proper permissions
chmod 755 "$BASE_DIR" -R
chmod +x "$INSTALL_DIR"/*.sh
chmod +x "$INSTALL_DIR"/*.py

# Make scripts executable
# chmod +x "$INSTALL_DIR/core/ap_manager.py"
# chmod +x "$INSTALL_DIR/cli/cli.py"
# chmod +x "$INSTALL_DIR/ap_manager.sh"
chmod +x "$INSTALL_DIR/sudors_edit.sh"
chmod +x "$INSTALL_DIR/deps.sh"

# Create symlink in /usr/local/bin for easy access
ln -sf "$INSTALL_DIR/cli/cli.py" /usr/local/bin/ap_manager

echo "Setting up sodors ..."
# "$INSTALL_DIR/sudors_edit.sh" install

# Install dependencies
echo "Installing dependencies..."
# "$INSTALL_DIR/deps.sh" install

# Create systemd service
cp ap_manager.service /etc/systemd/system/
systemctl daemon-reload

echo "Installation completed successfully!"
echo ""
echo "Usage examples:"
echo "  sudo ap_manager hotspot start          # Start hotspot"
echo "  sudo ap_manager config configure       # Modify/update/edit configuration"
echo "  sudo ap_manager hotspot status         # Check status"
echo "  sudo ap_manager hotspot stop           # Stop hotspot"
echo ""
echo "To enable automatic startup:"
echo -e "  systemctl enable $BLUE ap_manager.service $NC"
