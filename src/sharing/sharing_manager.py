"""
Sharing manager - coordinates all sharing functionality.
"""

import logging
from typing import Optional, List

from .hotspot import HotspotManager
from .onedrive import OneDriveUploader
from .qr_generator import QRGenerator


logger = logging.getLogger(__name__)


class SharingManager:
    """
    High-level manager for all photo sharing functionality.
    Coordinates hotspot, QR codes, and cloud upload.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize sharing manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.sharing_config = self.config.get('sharing', {})
        
        self._hotspot: Optional[HotspotManager] = None
        self._onedrive: Optional[OneDriveUploader] = None
        self._qr_generator = QRGenerator()
        
        self._web_url: Optional[str] = None
    
    def initialize(self) -> bool:
        """
        Initialize sharing components.
        
        Returns:
            True if initialization successful
        """
        success = True
        
        # Initialize hotspot if enabled
        if self.sharing_config.get('hotspot_enabled', False):
            self._hotspot = HotspotManager(self.config)
            if not self._hotspot.start():
                logger.warning("Failed to start hotspot - continuing without hotspot")
        
        # Initialize OneDrive if configured
        if self.sharing_config.get('onedrive_enabled', False):
            self._onedrive = OneDriveUploader(self.config)
            if not self._onedrive.is_configured():
                logger.warning("OneDrive not configured")
        
        return success
    
    def shutdown(self) -> None:
        """Shutdown sharing components."""
        if self._hotspot:
            self._hotspot.stop()
    
    def set_web_url(self, url: str) -> None:
        """
        Set the web server URL for QR code generation.
        
        Args:
            url: Web server URL
        """
        self._web_url = url
    
    def get_wifi_qr_data(self) -> Optional[str]:
        """
        Get WiFi QR code data string.
        
        Returns:
            WiFi QR code formatted string
        """
        if self._hotspot:
            return self._hotspot.get_wifi_qr_string()
        return None
    
    def get_download_url(self) -> Optional[str]:
        """
        Get the download URL.
        
        Returns:
            URL string
        """
        return self._web_url
    
    def generate_wifi_qr_image(self):
        """
        Generate WiFi QR code image.
        
        Returns:
            PIL Image of WiFi QR code
        """
        if not self._hotspot:
            return None
        
        return self._qr_generator.generate_wifi_qr(
            self._hotspot.get_ssid(),
            self._hotspot.get_password()
        )
    
    def generate_download_qr_image(self):
        """
        Generate download URL QR code image.
        
        Returns:
            PIL Image of download URL QR code
        """
        if not self._web_url:
            return None
        
        return self._qr_generator.generate_url_qr(self._web_url)
    
    def upload_to_onedrive(self, photo_paths: List[str],
                          completion_callback=None) -> None:
        """
        Upload photos to OneDrive asynchronously.
        
        Args:
            photo_paths: List of photo file paths
            completion_callback: Called with share URL on completion
        """
        if not self._onedrive or not self._onedrive.is_configured():
            if completion_callback:
                completion_callback(None)
            return
        
        self._onedrive.upload_photos_async(photo_paths, completion_callback)
    
    def is_hotspot_active(self) -> bool:
        """Check if hotspot is active."""
        return self._hotspot is not None and self._hotspot.is_active()
    
    def is_onedrive_configured(self) -> bool:
        """Check if OneDrive is configured."""
        return self._onedrive is not None and self._onedrive.is_configured()
    
    def get_hotspot_info(self) -> dict:
        """
        Get hotspot connection information.
        
        Returns:
            Dictionary with SSID, password, and IP
        """
        if not self._hotspot:
            return {}
        
        return {
            'ssid': self._hotspot.get_ssid(),
            'password': self._hotspot.get_password(),
            'ip': self._hotspot.get_ip_address()
        }
