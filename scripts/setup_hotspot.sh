#!/bin/bash

# WiFi Hotspot Setup Script for Raspberry Pi
# Configures hostapd and dnsmasq for photo sharing

set -e

echo "Setting up WiFi Hotspot..."

# Default settings
INTERFACE="${1:-wlan0}"
SSID="${2:-PhotoBooth}"
PASSWORD="${3:-photos123}"
CHANNEL="${4:-7}"

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "Warning: Not running on Raspberry Pi. Skipping hotspot setup."
    exit 0
fi

if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "Warning: Not running on Raspberry Pi. Skipping hotspot setup."
    exit 0
fi

# Stop services
sudo systemctl stop hostapd 2>/dev/null || true
sudo systemctl stop dnsmasq 2>/dev/null || true

# Backup existing configs
sudo cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.backup 2>/dev/null || true
sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null || true

# Configure static IP for interface
echo "Configuring network interface..."
sudo tee /etc/dhcpcd.conf.d/photobooth.conf > /dev/null << EOF
interface $INTERFACE
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

# Configure hostapd
echo "Configuring hostapd..."
sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
interface=$INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=$CHANNEL
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Point hostapd to config
sudo sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

# Configure dnsmasq
echo "Configuring dnsmasq..."
sudo tee /etc/dnsmasq.d/photobooth.conf > /dev/null << EOF
interface=$INTERFACE
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/photobooth.local/192.168.4.1
EOF

# Unmask and enable services
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

# Enable IP forwarding (optional, for internet sharing)
echo "Enabling IP forwarding..."
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf

echo ""
echo "Hotspot configuration complete!"
echo ""
echo "Settings:"
echo "  SSID:     $SSID"
echo "  Password: $PASSWORD"
echo "  IP:       192.168.4.1"
echo ""
echo "Reboot for changes to take effect, or run:"
echo "  sudo systemctl restart dhcpcd"
echo "  sudo systemctl start hostapd"
echo "  sudo systemctl start dnsmasq"
echo ""
