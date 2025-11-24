#!/bin/bash

echo "🔧 Installing Nail AR systemd service..."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    echo "   Run: sudo ./install_service.sh"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
PROJECT_DIR="/home/$ACTUAL_USER/nail-project"

echo "📁 Project directory: $PROJECT_DIR"
echo "👤 User: $ACTUAL_USER"
echo ""

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Check if start_app.sh exists
if [ ! -f "$PROJECT_DIR/start_app.sh" ]; then
    echo "❌ start_app.sh not found in $PROJECT_DIR"
    exit 1
fi

# Make start_app.sh executable
chmod +x "$PROJECT_DIR/start_app.sh"
echo "✅ Made start_app.sh executable"

# Copy service file to systemd
cp "$PROJECT_DIR/nail-ar.service" /etc/systemd/system/nail-ar.service
echo "✅ Copied service file to /etc/systemd/system/"

# Reload systemd
systemctl daemon-reload
echo "✅ Reloaded systemd"

# Enable service (start on boot)
systemctl enable nail-ar.service
echo "✅ Enabled nail-ar service (will start on boot)"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  Installation Complete! ✅                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Available commands:"
echo ""
echo "  Start service:    sudo systemctl start nail-ar"
echo "  Stop service:     sudo systemctl stop nail-ar"
echo "  Restart service:  sudo systemctl restart nail-ar"
echo "  Check status:     sudo systemctl status nail-ar"
echo "  View logs:        sudo journalctl -u nail-ar -f"
echo "  Disable autostart: sudo systemctl disable nail-ar"
echo ""
echo "The service will now start automatically on system boot!"
echo ""
echo "To start it now, run: sudo systemctl start nail-ar"
