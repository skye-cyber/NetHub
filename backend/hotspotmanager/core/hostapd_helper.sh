#!/bin/bash
# /usr/local/bin/ap-manager-hostapd.sh
# AP Manager Hostapd Control Script

set -e  # Exit on error

CONFIG_DIR="/etc/ap_manager/conf"
HOSTAPD_CONF="$CONFIG_DIR/hostapd.conf"
PID_FILE="/run/ap_manager/hostapd.pid"
LOG_FILE="/etc/ap_manager/hostapd.log"
INTERFACE="xap0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Error function
error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Check if interface exists
check_interface() {
    if ! ip link show "$INTERFACE" >/dev/null 2>&1; then
        error "Interface $INTERFACE does not exist. Run WiFi initialization first."
    fi
}

# Check if interface is up
check_interface_up() {
    if ! ip link show "$INTERFACE" | grep -q "state UP"; then
        log "${YELLOW}Bringing interface $INTERFACE up...${NC}"
        ip link set "$INTERFACE" up
        sleep 1
    fi
}

# Check if hostapd is already running
is_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            return 0  # Running
        fi
    fi
    return 1  # Not running
}

# Start hostapd
start() {
    log "${GREEN}Starting hostapd...${NC}"

    check_interface
    # check_interface_up

    if is_running; then
        log "${YELLOW}hostapd is already running (PID: $(cat $PID_FILE))${NC}"
        return 0
    fi

    # Ensure config exists
    if [ ! -f "$HOSTAPD_CONF" ]; then
        error "hostapd config not found: $HOSTAPD_CONF"
    fi

    # Ensure PID directory exists
    mkdir -p "$(dirname "$PID_FILE")"

    # Start hostapd with options
    local debug_flag=""
    if [ "$DEBUG" = "true" ]; then
        debug_flag="-d"
        log "${YELLOW}Running in debug mode${NC}"
    fi

    sudo rfkill unblock wlan
    # Start hostapd
    if [ "$DAEMON" = "true" ]; then
        # Daemon mode (background with PID file)
        log "Starting hostapd in daemon mode..."
        hostapd -B "$debug_flag" -P "$PID_FILE" "$HOSTAPD_CONF" > "$LOG_FILE" 2>&1

        # Wait for PID file
        local count=0
        while [ ! -f "$PID_FILE" ] && [ $count -lt 10 ]; do
            sleep 0.5
            count=$((count + 1))
        done

        if [ -f "$PID_FILE" ]; then
            pid=$(cat "$PID_FILE")
            if kill -0 "$pid" 2>/dev/null; then
                log "${GREEN}hostapd started successfully (PID: $pid)${NC}"
                return 0
            fi
        fi

        error "Failed to start hostapd. Check $LOG_FILE"

    else
        # Foreground mode (for debugging)
        log "Starting hostapd in foreground mode..."
        echo "sudo /usr/bin/stdbuf -oL hostapd $debug_flag $HOSTAPD_CONF"
        sudo /usr/bin/stdbuf -oL hostapd $debug_flag $HOSTAPD_CONF -B
    fi
}

# Stop hostapd
stop() {
    log "${YELLOW}Stopping hostapd...${NC}"

    if ! is_running; then
        log "hostapd is not running"
        return 0
    fi

    pid=$(cat "$PID_FILE")

    # Try SIGTERM first (graceful shutdown)
    log "Sending SIGTERM to PID $pid"
    kill -TERM "$pid" 2>/dev/null || true

    # Wait for process to exit
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
        sleep 0.5
        count=$((count + 1))
    done

    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
        log "Sending SIGKILL to PID $pid"
        kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    fi

    # Remove PID file
    rm -f "$PID_FILE"

    log "${GREEN}hostapd stopped${NC}"
}

# Restart hostapd
restart() {
    stop
    sleep 2
    start
}

# Status check
status() {
    if is_running; then
        pid=$(cat "$PID_FILE")
        log "${GREEN}hostapd is running (PID: $pid)${NC}"
        return 0
    else
        log "${RED}hostapd is not running${NC}"
        return 1
    fi
}

# Reload config (SIGHUP)
reload() {
    if ! is_running; then
        error "hostapd is not running"
    fi

    pid=$(cat "$PID_FILE")
    log "Reloading hostapd config (PID: $pid)"
    kill -HUP "$pid"
    log "${GREEN}Config reload signal sent${NC}"
}

# Show logs
logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        log "No log file found: $LOG_FILE"
    fi
}

# Main script logic
main() {
    ACTION="${1:-start}"
    DAEMON="false"
    DEBUG="false"

    # Parse additional arguments
    shift
    while [ $# -gt 0 ]; do
        case "$1" in
            --daemon)
                DAEMON="true"
                shift
                ;;
            --debug)
                DEBUG="true"
                shift
                ;;
            --interface=*)
                INTERFACE="${1#*=}"
                shift
                ;;
            --config=*)
                HOSTAPD_CONF="${1#*=}"
                shift
                ;;
            *)
                log "${YELLOW}Unknown option: $1${NC}"
                shift
                ;;
        esac
    done

    case "$ACTION" in
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        status)
            status
            ;;
        reload)
            reload
            ;;
        logs)
            logs
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|reload|logs} [--daemon] [--debug]"
            echo "Options:"
            echo "  --daemon     Run in background (default: foreground)"
            echo "  --debug      Enable debug output"
            echo "  --interface= Network interface (default: xap0)"
            echo "  --config=    Config file path"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
