#!/bin/bash

# Installation script for Custom Hotspot Manager

set -e

echo "Installing Custom ap_manager Manager..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Create installation directory
INSTALL_DIR="/opt/ap_manager"
mkdir -p "$INSTALL_DIR"

# Copy files
cp ap_cli.py "$INSTALL_DIR/"
cp ap_manager.py "$INSTALL_DIR/"
cp ap_manager.sh "$INSTALL_DIR/"
cp sudoer_edit.sh "$INSTALL_DIR/"

# Make scripts executable
chmod +x "$INSTALL_DIR/ap_manager.py"
chmod +x "$INSTALL_DIR/ap_cli.py"
chmod +x "$INSTALL_DIR/ap_manager.sh"
chmod +x "$INSTALL_DIR/sudoer_edit.sh"

# Create symlink in /usr/local/bin for easy access
ln -sf "$INSTALL_DIR/ap_manager.sh" /usr/local/bin/ap_manager

# Install dependencies
echo "Installing dependencies..."
"$INSTALL_DIR/ap_manager.sh" install

# Create systemd service
cp ap_manager.service /etc/systemd/system/
systemctl daemon-reload

echo "Installation completed successfully!"
echo ""
echo "Usage examples:"
echo "  ap_manager start          # Start hotspot"
echo "  ap_manager configure      # Interactive configuration"
echo "  ap_manager status         # Check status"
echo "  ap_manager stop           # Stop hotspot"
echo ""
echo "To enable automatic startup:"
echo "  systemctl enable ap_manager.service"
