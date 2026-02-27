#!/bin/bash

# Open-Imagebox Installation Script
# For Raspberry Pi OS (Bullseye or newer)

set -e

echo "=============================================="
echo "  Open-Imagebox Photo Booth Installation"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run as root. Run as normal user."
    exit 1
fi

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project directory: $PROJECT_DIR"
echo ""

# Update system
echo "[1/7] Updating system packages..."
sudo apt-get update

# Install system dependencies
echo ""
echo "[2/7] Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-pyqt5 \
    gphoto2 \
    libgphoto2-dev \
    hostapd \
    dnsmasq \
    qrencode \
    libzbar0 \
    libjpeg-dev \
    libopenjp2-7 \
    libtiff5

# Create virtual environment
echo ""
echo "[3/7] Creating Python virtual environment..."
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo ""
echo "[4/7] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo ""
echo "[5/7] Creating required directories..."
mkdir -p ~/photos
mkdir -p ~/sessions
mkdir -p ~/.config/open-imagebox

# Copy configuration
echo ""
echo "[6/7] Setting up configuration..."
if [ ! -f "$PROJECT_DIR/settings/config.json" ]; then
    cp "$PROJECT_DIR/settings/config.example.json" "$PROJECT_DIR/settings/config.json"
    echo "Created config.json from example. Please edit settings/config.json"
fi

# Setup hotspot (optional)
echo ""
echo "[7/7] Configuring hotspot..."
"$SCRIPT_DIR/setup_hotspot.sh" || echo "Hotspot setup skipped (may require manual configuration)"

# Create systemd service
echo ""
echo "Creating systemd service..."
sudo tee /etc/systemd/system/open-imagebox.service > /dev/null << EOF
[Unit]
Description=Open-Imagebox Photo Booth
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python -m src.main
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo "Systemd service created. Enable with: sudo systemctl enable open-imagebox"

# Done
echo ""
echo "=============================================="
echo "  Installation Complete!"
echo "=============================================="
echo ""
echo "To start the photo booth:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  python -m src.main"
echo ""
echo "Or enable automatic startup:"
echo "  sudo systemctl enable open-imagebox"
echo "  sudo systemctl start open-imagebox"
echo ""
echo "Edit configuration at:"
echo "  $PROJECT_DIR/settings/config.json"
echo ""
