#!/bin/bash

# Installation script for Custom Hotspot Manager

set -e

echo "Installing Custom Hotspot Manager..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Create installation directory
INSTALL_DIR="/opt/custom-hotspot"
mkdir -p "$INSTALL_DIR"

# Copy files
cp hotspot_manager.py "$INSTALL_DIR/"
cp hotspot.sh "$INSTALL_DIR/"

# Make scripts executable
chmod +x "$INSTALL_DIR/hotspot_manager.py"
chmod +x "$INSTALL_DIR/hotspot.sh"

# Create symlink in /usr/local/bin for easy access
ln -sf "$INSTALL_DIR/hotspot.sh" /usr/local/bin/hotspot

# Install dependencies
echo "Installing dependencies..."
"$INSTALL_DIR/hotspot.sh" install

# Create systemd service
cp hotspot.service /etc/systemd/system/
systemctl daemon-reload

echo "Installation completed successfully!"
echo ""
echo "Usage examples:"
echo "  hotspot start          # Start hotspot"
echo "  hotspot configure      # Interactive configuration"
echo "  hotspot status         # Check status"
echo "  hotspot stop           # Stop hotspot"
echo ""
echo "To enable automatic startup:"
echo "  systemctl enable hotspot.service"
