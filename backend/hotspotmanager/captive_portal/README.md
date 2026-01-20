# Captive Portal System

A sophisticated captive portal implementation that provides network access control with user authentication, built with Python Flask, iptables, and modern web technologies.

## Features

- **🔐 MAC-based Authentication** - Secure device authentication
- **🌐 Automatic Redirection** - Seamless captive portal detection
- **📊 Real-time Dashboard** - Beautiful statistics and monitoring
- **⚡ Instant Access** - No reconnect required after authentication
- **📱 Responsive Design** - Works on all devices
- **🔒 Firewall Integration** - iptables-based access control
- **📈 Connection Analytics** - Live connection statistics
- **🎯 Customizable Portal** - Easy to brand and customize

## Architecture

```
Client Device → Hotspot (ap0) → Captive Portal → Internet (eth0)
                    │
                    ├── MAC Authentication
                    ├── Firewall Rules
                    ├── Traffic Redirection
                    └── Connection Tracking
```

## Prerequisites

- Linux system with iptables
- Python 3.8+
- Network interfaces: `ap0` (hotspot) and `eth0` (internet)
- Root privileges for firewall configuration

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd captive
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up directory structure:**
```bash
mkdir -p auth logs scripts
```

4. **Configure network interfaces:**
Ensure you have:
- `ap0` as your hotspot interface
- `eth0` as your internet-facing interface

## Project Structure

```
captive/
├── app.py
├── auth
│   ├── authenticated_macs
│   ├── authenticated_macs.backup
│   └── device_history.csv
├── logs
│   ├── captive.log
│   ├── captive_setup.log
│   ├── device_detection.log
│   ├── device_scanner.log
│   ├── dnsmasq.log
│   ├── firewall.log
│   └── flask.log
├── README.md
├── requirements.txt
├── scripts
│   ├── captive_portal.sh
│   ├── check_access.sh
│   ├── clean_reset.sh
│   ├── debug_internet.sh
│   ├── debug_redirect.sh
│   ├── detect_devices.sh
│   ├── firewall_rules.sh
│   ├── integrity_test.sh
│   ├── monitor_devices.sh
│   ├── setup_captive.sh
│   └── update_firewall.sh
├── static
│   ├── css
│   │   ├── dash.css
│   │   └── style.css
│   └── js
│       ├── dash.js
│       └── script.js
├── templates
│   ├── admin.html
│   ├── dashboard.html
│   └── portal.html
└── utils
    ├── device_scanner.py
    └── helpers.py
```

## Usage

```bash
Usage: captive {start|stop|status|test|monitor|check|firewall-rules|reset}
```

### Command Details

#### `captive start`
Starts the captive portal system.
```bash
sudo captive start
```
**Actions:**
- Initializes firewall rules
- Starts Flask application on port 8181
- Enables IP forwarding
- Sets up NAT redirection
- Begins monitoring connections

#### `captive stop`
Stops the captive portal system.
```bash
sudo captive stop
```
**Actions:**
- Stops Flask application
- Cleans up firewall rules
- Disables redirection
- Preserves authenticated MACs

#### `captive status`
Displays system status and current connections.
```bash
captive status
```
**Output:**
- Service status (running/stopped)
- Number of authenticated devices
- Active connections
- System resource usage

#### `captive test`
Tests the captive portal functionality.
```bash
sudo captive test
```
**Tests:**
- Firewall rule validation
- Portal accessibility
- Authentication flow
- Internet connectivity for authenticated devices

#### `captive monitor`
Real-time monitoring of portal activity.
```bash
captive monitor
```
**Monitors:**
- New connection attempts
- Authentication events
- Bandwidth usage
- System logs

#### `captive check`
Comprehensive system health check.
```bash
sudo captive check
```
**Checks:**
- Network interface status
- Firewall rule integrity
- Database consistency
- Service dependencies

#### `captive firewall-rules`
Displays current firewall configuration.
```bash
sudo captive firewall-rules
```
**Shows:**
- CAPTIVE_PORTAL chain rules
- AUTH_REDIRECT NAT rules
- PREROUTING configurations
- Active MAC-based rules

#### `captive reset`
Completely resets the system.
```bash
sudo captive reset
```
**WARNING:** This will:
- Clear all firewall rules
- Remove all authenticated MACs
- Reset all configurations
- Stop all services

## Configuration

### Network Settings
Edit the setup script to match your network:
```bash
# Interface facing the clients (your hotspot interface)
CLIENT_IFACE="ap0"

# Interface facing the internet  
INTERNET_IFACE="eth0"

# Gateway IP for the captive portal
GATEWAY_IP="192.168.12.1"

# Flask server port
FLASK_PORT="8181"
```

### Customization

#### Portal Branding
Modify `templates/login.html`:
- Company logo
- Color scheme
- Welcome message
- Terms of service

#### Authentication Logic
Edit `app.py` to implement your authentication:
```python
def authenticate_mac(mac_address):
    # Add your authentication logic
    # Example: Check against database, API, etc.
    return True  # or False based on your logic
```

#### Dashboard Features
Customize `templates/dashboard.html`:
- Additional statistics
- Company branding
- Custom actions/buttons
- Connection information

## API Endpoints

### `POST /connect`
Authenticates a device and grants internet access.

**Response:**
```json
{
    "status": "success",
    "message": "Access granted! Welcome to the network.",
    "dashboard": true,
    "redirect_url": "/dashboard",
    "client_mac": "aa:bb:cc:dd:ee:ff",
    "client_ip": "192.168.12.100"
}
```

### `GET /dashboard`
Displays the post-authentication dashboard with connection statistics.

### `GET /`
Main captive portal login page.

## Firewall Architecture

### Chains Created:
- **CAPTIVE_PORTAL**: Filters forwarded traffic based on MAC authentication
- **AUTH_REDIRECT**: NAT chain for HTTP/HTTPS redirection bypass

### Rule Flow:
1. **New Device**: HTTP/HTTPS → AUTH_REDIRECT → Portal (8181)
2. **Authenticated**: MAC matches → RETURN → Internet access
3. **Unauthenticated**: No MAC match → REDIRECT → Portal

## Monitoring & Logging

### Connection Tracking
- Real-time MAC authentication logging
- Connection state monitoring
- Bandwidth usage statistics

### System Logs
- Authentication attempts
- Firewall rule changes
- System errors and warnings

## Troubleshooting

### Common Issues

1. **No Captive Portal Detection**
   ```bash
   captive check
   captive firewall-rules
   ```

2. **Authenticated Devices No Internet**
   ```bash
   captive test
   captive monitor
   ```

3. **Service Not Starting**
   ```bash
   captive status
   journalctl -u captive-portal
   ```

### Debug Commands

Check firewall rules:
```bash
iptables -L CAPTIVE_PORTAL -n --line-numbers
iptables -t nat -L AUTH_REDIRECT -n --line-numbers
```

Monitor connections:
```bash
conntrack -L
tail -f /var/log/captive.log
```

## Security Features

- MAC address validation
- Connection state tracking
- Secure redirect handling
- Isolated network segmentation
- Regular security updates

## Performance

- Handles 100+ concurrent connections
- Low latency authentication
- Efficient connection tracking
- Minimal resource footprint

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and documentation:
- Check the troubleshooting section
- Review firewall configuration
- Monitor system logs
- Test individual components

## Development

### Running in Development Mode
```bash
python app.py --debug
```

### Testing New Features
```bash
captive test
captive monitor
```

### Building Custom Versions
Modify the setup scripts and templates to match your specific requirements.

---

**Note:** This system requires proper network configuration and should be tested in a controlled environment before production deployment.
