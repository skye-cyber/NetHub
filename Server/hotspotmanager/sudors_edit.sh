#!/bin/bash
# Execute ap_manager without asking password
# This script must be run as root

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Check if ap_manager is installed in the correct location
AP_MANAGER_PATH="/usr/local/bin/ap_manager"

if [[ ! -f "$AP_MANAGER_PATH" ]]; then
    echo "ap_manager not found at $AP_MANAGER_PATH"
    exit 1
fi

# Add sudo rule for ap_manager
echo "Adding sudo rule for ap_manager..."
echo "ALL ALL=NOPASSWD: $AP_MANAGER_PATH" | EDITOR='tee -a' visudo -f /etc/sudoers.d/ap_manager

# Set proper permissions for the sudoers file
chmod 440 /etc/sudoers.d/ap_manager

echo "Sudo rule added successfully"
