"""
QR code generator for WiFi connection and photo sharing.
"""

import logging
from typing import Optional, Tuple
import io

try:
    import qrcode
    from PIL import Image
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


logger = logging.getLogger(__name__)


class QRGenerator:
    """
    Generates QR codes for WiFi connection and URL sharing.
    """
    
    def __init__(self):
        """Initialize QR generator."""
        if not QRCODE_AVAILABLE:
            logger.warning("qrcode library not available. "
                         "Install with: pip install qrcode[pil]")
    
    def generate_wifi_qr(self, ssid: str, password: str, 
                        security: str = "WPA") -> Optional[Image.Image]:
        """
        Generate a QR code for WiFi connection.
        
        Args:
            ssid: WiFi network name
            password: WiFi password
            security: Security type (WPA, WEP, or empty for open)
        
        Returns:
            PIL Image of QR code, or None on failure
        """
        if not QRCODE_AVAILABLE:
            return None
        
        # WiFi QR code format: WIFI:T:WPA;S:ssid;P:password;;
        wifi_string = f"WIFI:T:{security};S:{ssid};P:{password};;"
        
        return self._generate_qr(wifi_string)
    
    def generate_url_qr(self, url: str) -> Optional[Image.Image]:
        """
        Generate a QR code for a URL.
        
        Args:
            url: URL to encode
        
        Returns:
            PIL Image of QR code, or None on failure
        """
        if not QRCODE_AVAILABLE:
            return None
        
        return self._generate_qr(url)
    
    def _generate_qr(self, data: str, 
                     size: Tuple[int, int] = (300, 300)) -> Optional[Image.Image]:
        """
        Generate a QR code image.
        
        Args:
            data: Data to encode
            size: Output image size (width, height)
        
        Returns:
            PIL Image of QR code, or None on failure
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize if needed
            if img.size != size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            
            return img
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            return None
    
    def save_qr(self, data: str, filename: str, 
                size: Tuple[int, int] = (300, 300)) -> bool:
        """
        Generate and save a QR code to file.
        
        Args:
            data: Data to encode
            filename: Output filename
            size: Output image size
        
        Returns:
            True if saved successfully
        """
        img = self._generate_qr(data, size)
        if img is None:
            return False
        
        try:
            img.save(filename)
            return True
        except Exception as e:
            logger.error(f"Failed to save QR code: {e}")
            return False
    
    def get_qr_bytes(self, data: str, 
                     format: str = "PNG") -> Optional[bytes]:
        """
        Generate a QR code and return as bytes.
        
        Args:
            data: Data to encode
            format: Image format (PNG, JPEG, etc.)
        
        Returns:
            Image bytes, or None on failure
        """
        img = self._generate_qr(data)
        if img is None:
            return None
        
        try:
            buffer = io.BytesIO()
            img.save(buffer, format=format)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Failed to convert QR to bytes: {e}")
            return None
