"""
Camera manager for handling camera connections and operations.
"""

import logging
from typing import Optional
import numpy as np

from .camera_base import CameraBase
from .gphoto2_camera import GPhoto2Camera


logger = logging.getLogger(__name__)


class CameraManager:
    """
    Manages camera connections and provides a unified interface.
    Supports automatic reconnection and camera type detection.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize the camera manager.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config or {}
        self.camera_config = self.config.get('camera', {})
        self._camera: Optional[CameraBase] = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
    
    def initialize(self) -> bool:
        """
        Initialize and connect to the camera.
        
        Returns:
            True if camera connected successfully.
        """
        camera_type = self.camera_config.get('type', 'gphoto2')
        
        logger.info(f"Initializing camera (type: {camera_type})")
        
        if camera_type == 'gphoto2':
            self._camera = GPhoto2Camera(self.camera_config)
        else:
            logger.error(f"Unknown camera type: {camera_type}")
            return False
        
        return self._camera.connect()
    
    def shutdown(self) -> None:
        """Disconnect and cleanup the camera."""
        if self._camera is not None:
            self._camera.disconnect()
            self._camera = None
    
    def get_preview_frame(self) -> Optional[np.ndarray]:
        """
        Get a preview frame from the camera.
        
        Returns:
            Preview frame as numpy array, or None.
        """
        if self._camera is None:
            return None
        
        frame = self._camera.get_preview_frame()
        
        # Reset reconnect counter on successful frame
        if frame is not None:
            self._reconnect_attempts = 0
        
        return frame
    
    def capture_image(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Capture a full resolution image.
        
        Args:
            filename: Optional filename to save the image to.
        
        Returns:
            Path to captured image, or None on failure.
        """
        if self._camera is None:
            return None
        
        return self._camera.capture_image(filename)
    
    def auto_focus(self) -> bool:
        """Trigger auto focus."""
        if self._camera is None:
            return False
        return self._camera.auto_focus()
    
    def is_connected(self) -> bool:
        """Check if camera is connected."""
        return self._camera is not None and self._camera.is_connected()
    
    def try_reconnect(self) -> bool:
        """
        Attempt to reconnect to the camera.
        
        Returns:
            True if reconnection successful.
        """
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return False
        
        self._reconnect_attempts += 1
        logger.info(f"Reconnection attempt {self._reconnect_attempts}/"
                   f"{self._max_reconnect_attempts}")
        
        # Disconnect first
        if self._camera is not None:
            self._camera.disconnect()
        
        # Try to reconnect
        if self.initialize():
            self._reconnect_attempts = 0
            return True
        
        return False
    
    def get_camera_info(self) -> dict:
        """Get camera information."""
        if self._camera is None:
            return {}
        return self._camera.get_camera_info()
