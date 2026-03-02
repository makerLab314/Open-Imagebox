"""
WiFi Hotspot manager for Raspberry Pi.
Creates a WiFi access point for mobile devices to connect and download photos.
"""

import subprocess
import logging
import os
from typing import Optional


logger = logging.getLogger(__name__)


class HotspotManager:
    """
    Manages WiFi hotspot functionality on Raspberry Pi.
    Uses hostapd and dnsmasq for AP mode.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize hotspot manager.
        
        Args:
            config: Configuration dictionary with hotspot settings
        """
        self.config = config or {}
        self.sharing_config = self.config.get('sharing', {})
        
        self._ssid = self.sharing_config.get('hotspot_ssid', 'PhotoBooth')
        self._password = self.sharing_config.get('hotspot_password', 'photos123')
        self._interface = self.sharing_config.get('hotspot_interface', 'wlan0')
        self._ip_address = '192.168.4.1'
        self._is_active = False
    
    def start(self) -> bool:
        """
        Start the WiFi hotspot.
        
        Returns:
            True if hotspot started successfully
        """
        if self._is_active:
            logger.info("Hotspot already active")
            return True
        
        try:
            # Check if we're on a Raspberry Pi
            if not self._is_raspberry_pi():
                logger.warning("Not running on Raspberry Pi, hotspot simulation mode")
                self._is_active = True
                return True
            
            # Create hostapd config
            self._create_hostapd_config()
            
            # Create dnsmasq config
            self._create_dnsmasq_config()
            
            # Stop any existing services
            subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'], 
                         capture_output=True)
            subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'], 
                         capture_output=True)
            
            # Configure interface
            subprocess.run([
                'sudo', 'ip', 'addr', 'flush', 'dev', self._interface
            ], capture_output=True)
            
            subprocess.run([
                'sudo', 'ip', 'addr', 'add', 
                f'{self._ip_address}/24', 
                'dev', self._interface
            ], capture_output=True)
            
            subprocess.run([
                'sudo', 'ip', 'link', 'set', self._interface, 'up'
            ], capture_output=True)
            
            # Start services
            result = subprocess.run([
                'sudo', 'systemctl', 'start', 'hostapd'
            ], capture_output=True)
            
            if result.returncode != 0:
                stderr_output = result.stderr.decode()
                if 'masked' in stderr_output:
                    logger.warning(
                        "hostapd service is masked. Run: sudo systemctl unmask hostapd"
                    )
                else:
                    logger.error(f"Failed to start hostapd: {stderr_output}")
                return False
            
            result = subprocess.run([
                'sudo', 'systemctl', 'start', 'dnsmasq'
            ], capture_output=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to start dnsmasq: {result.stderr.decode()}")
                return False
            
            self._is_active = True
            logger.info(f"Hotspot started: {self._ssid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start hotspot: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop the WiFi hotspot.
        
        Returns:
            True if hotspot stopped successfully
        """
        if not self._is_active:
            return True
        
        try:
            if self._is_raspberry_pi():
                subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'], 
                             capture_output=True)
                subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'], 
                             capture_output=True)
            
            self._is_active = False
            logger.info("Hotspot stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop hotspot: {e}")
            return False
    
    def is_active(self) -> bool:
        """Check if hotspot is active."""
        return self._is_active
    
    def get_ssid(self) -> str:
        """Get the hotspot SSID."""
        return self._ssid
    
    def get_password(self) -> str:
        """Get the hotspot password."""
        return self._password
    
    def get_ip_address(self) -> str:
        """Get the hotspot IP address."""
        return self._ip_address
    
    def get_wifi_qr_string(self) -> str:
        """
        Get the WiFi connection string for QR code.
        
        Returns:
            WiFi QR code formatted string
        """
        return f"WIFI:T:WPA;S:{self._ssid};P:{self._password};;"
    
    def _create_hostapd_config(self) -> None:
        """Create hostapd configuration file."""
        config_content = f"""interface={self._interface}
driver=nl80211
ssid={self._ssid}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={self._password}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        config_path = '/tmp/photobooth_hostapd.conf'
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Copy to system location with sudo
        subprocess.run([
            'sudo', 'cp', config_path, '/etc/hostapd/hostapd.conf'
        ], capture_output=True)
    
    def _create_dnsmasq_config(self) -> None:
        """Create dnsmasq configuration file."""
        config_content = f"""interface={self._interface}
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/photobooth.local/{self._ip_address}
"""
        config_path = '/tmp/photobooth_dnsmasq.conf'
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Copy to system location with sudo
        subprocess.run([
            'sudo', 'cp', config_path, '/etc/dnsmasq.d/photobooth.conf'
        ], capture_output=True)
    
    def _is_raspberry_pi(self) -> bool:
        """Check if running on a Raspberry Pi."""
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                return 'Raspberry Pi' in model
        except Exception:
            return False
