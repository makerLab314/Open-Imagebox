#!/bin/bash
# Open-Imagebox Installation Script
# For Raspberry Pi OS (Bullseye or newer)
# Inspired by the self-o-mat project (https://github.com/xtech/self-o-mat)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
step()  { echo -e "\n${BLUE}==== $1 ====${NC}"; }

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    error "Bitte nicht als root ausführen. Nutze deinen normalen Benutzer."
    error "Please do not run as root. Run as normal user."
    exit 1
fi

# Determine directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CURRENT_USER="$(whoami)"
HOME_DIR="$(eval echo ~$CURRENT_USER)"

echo ""
echo "=============================================="
echo "  Open-Imagebox Photo Booth Installation"
echo "  Inspiriert von self-o-mat"
echo "  (https://github.com/xtech/self-o-mat)"
echo "=============================================="
echo ""
info "Projektverzeichnis: $PROJECT_DIR"
info "Benutzer: $CURRENT_USER"
info "Home: $HOME_DIR"
echo ""

# ─── Step 1: System Update ───────────────────────────────────────────
step "[1/8] System aktualisieren / Updating system..."
sudo apt-get update -y || {
    warn "apt-get update hatte Probleme, versuche fortzufahren..."
}

# ─── Step 2: System Dependencies ─────────────────────────────────────
step "[2/8] Systemabhängigkeiten installieren / Installing system dependencies..."
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
    libtiff-dev \
    libatlas-base-dev \
    || {
    error "Paketinstallation fehlgeschlagen!"
    error "Package installation failed!"
    exit 1
}

# ─── Step 3: Kill interfering gphoto2 processes ──────────────────────
step "[3/8] gPhoto2 Hintergrundprozesse stoppen / Stopping gPhoto2 background processes..."
# gvfs-gphoto2-volume-monitor and gvfsd-gphoto2 lock the camera
# This is critical - without this, the camera cannot be accessed
sudo pkill -f gvfs-gphoto2-volume-monitor 2>/dev/null || true
sudo pkill -f gvfsd-gphoto2 2>/dev/null || true

# Prevent them from starting again
if [ -f /usr/lib/gvfs/gvfs-gphoto2-volume-monitor ]; then
    sudo chmod -x /usr/lib/gvfs/gvfs-gphoto2-volume-monitor 2>/dev/null || true
    info "gvfs-gphoto2-volume-monitor deaktiviert"
fi

# Also create a udev rule to prevent auto-mounting
UDEV_RULE="/etc/udev/rules.d/99-photobooth-camera.rules"
if [ ! -f "$UDEV_RULE" ]; then
    sudo tee "$UDEV_RULE" > /dev/null << 'UDEV_EOF'
# Prevent gvfs from claiming the camera for Open-Imagebox
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="04a9", TAG-="gphoto2"
UDEV_EOF
    sudo udevadm control --reload-rules 2>/dev/null || true
    info "udev-Regel für Kamera erstellt"
fi

# ─── Step 4: Python Virtual Environment ──────────────────────────────
step "[4/8] Python Virtual Environment erstellen / Creating Python venv..."
cd "$PROJECT_DIR"

if [ -d "venv" ]; then
    info "Vorhandenes venv gefunden, wird wiederverwendet"
else
    python3 -m venv --system-site-packages venv || {
        error "Virtual Environment konnte nicht erstellt werden!"
        exit 1
    }
fi

source venv/bin/activate

# ─── Step 5: Python Dependencies ─────────────────────────────────────
step "[5/8] Python-Abhängigkeiten installieren / Installing Python dependencies..."
pip install --upgrade pip setuptools wheel 2>/dev/null
pip install -r requirements.txt || {
    error "Python-Abhängigkeiten konnten nicht installiert werden!"
    exit 1
}

# ─── Step 6: Create Directories ──────────────────────────────────────
step "[6/8] Verzeichnisse erstellen / Creating directories..."
mkdir -p "$HOME_DIR/photos"
mkdir -p "$HOME_DIR/sessions"
mkdir -p "$HOME_DIR/.config/open-imagebox"
mkdir -p "$HOME_DIR/.local/share/open-imagebox/logs"

info "Foto-Verzeichnis: $HOME_DIR/photos"
info "Session-Verzeichnis: $HOME_DIR/sessions"

# ─── Step 7: Configuration ───────────────────────────────────────────
step "[7/8] Konfiguration einrichten / Setting up configuration..."
CONFIG_FILE="$PROJECT_DIR/settings/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    # Create config from example, replacing /home/pi with actual home
    sed "s|/home/pi|$HOME_DIR|g" "$PROJECT_DIR/settings/config.example.json" > "$CONFIG_FILE"
    info "config.json erstellt (basierend auf config.example.json)"
    info "Bitte bearbeite: $CONFIG_FILE"
else
    info "config.json existiert bereits, wird nicht überschrieben"
fi

# ─── Step 8: Systemd Service ─────────────────────────────────────────
step "[8/8] Systemd-Service einrichten / Setting up systemd service..."

sudo tee /etc/systemd/system/open-imagebox.service > /dev/null << EOF
[Unit]
Description=Open-Imagebox Photo Booth
After=network.target graphical.target
Wants=graphical.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=DISPLAY=:0
Environment=XAUTHORITY=$HOME_DIR/.Xauthority
Environment=QT_QPA_PLATFORM=xcb
ExecStartPre=/bin/bash -c 'pkill -f gvfs-gphoto2-volume-monitor || true'
ExecStartPre=/bin/bash -c 'pkill -f gvfsd-gphoto2 || true'
ExecStart=$PROJECT_DIR/venv/bin/python -m src.main
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable open-imagebox.service
info "Systemd-Service erstellt und aktiviert"

# ─── Optional: Hotspot Setup ─────────────────────────────────────────
echo ""
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    info "Raspberry Pi erkannt - Hotspot wird konfiguriert..."
    bash "$SCRIPT_DIR/setup_hotspot.sh" || {
        warn "Hotspot-Setup fehlgeschlagen. Kann später manuell konfiguriert werden."
        warn "Hotspot setup failed. Can be configured manually later."
    }
else
    info "Kein Raspberry Pi erkannt - Hotspot-Setup übersprungen"
    info "Not running on Raspberry Pi - Hotspot setup skipped"
fi

# ─── Done ─────────────────────────────────────────────────────────────
echo ""
echo "=============================================="
echo -e "  ${GREEN}Installation abgeschlossen!${NC}"
echo -e "  ${GREEN}Installation Complete!${NC}"
echo "=============================================="
echo ""
echo "┌─────────────────────────────────────────────┐"
echo "│  Nächste Schritte / Next Steps:             │"
echo "├─────────────────────────────────────────────┤"
echo "│                                             │"
echo "│  1. Kamera per USB anschließen              │"
echo "│     Connect camera via USB                  │"
echo "│                                             │"
echo "│  2. Konfiguration anpassen:                 │"
echo "│     Edit configuration:                     │"
echo "│     nano $PROJECT_DIR/settings/config.json"
echo "│                                             │"
echo "│  3. Photo Booth starten:                    │"
echo "│     Start Photo Booth:                      │"
echo "│                                             │"
echo "│     cd $PROJECT_DIR"
echo "│     source venv/bin/activate                │"
echo "│     python -m src.main                      │"
echo "│                                             │"
echo "│  Oder automatisch beim Booten:              │"
echo "│  Or start automatically on boot:            │"
echo "│                                             │"
echo "│     sudo systemctl start open-imagebox      │"
echo "│                                             │"
echo "│  Status prüfen / Check status:              │"
echo "│     sudo systemctl status open-imagebox     │"
echo "│                                             │"
echo "│  Logs ansehen / View logs:                  │"
echo "│     journalctl -u open-imagebox -f          │"
echo "│                                             │"
echo "└─────────────────────────────────────────────┘"
echo ""
