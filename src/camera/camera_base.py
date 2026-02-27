"""
Abstract base class for camera implementations.
Inspired by self-o-mat's camera interface design.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np


class CameraBase(ABC):
    """Abstract base class for camera implementations."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the camera."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the camera."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if camera is connected."""
        pass
    
    @abstractmethod
    def get_preview_frame(self) -> Optional[np.ndarray]:
        """Get a single preview frame from the camera."""
        pass
    
    @abstractmethod
    def capture_image(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Capture a full resolution image.
        
        Args:
            filename: Optional filename to save the image to.
                     If None, a temporary file is used.
        
        Returns:
            Path to the captured image file, or None on failure.
        """
        pass
    
    @abstractmethod
    def get_camera_info(self) -> dict:
        """Get camera information (model, serial, etc.)."""
        pass
    
    @abstractmethod
    def auto_focus(self) -> bool:
        """Trigger auto focus."""
        pass
    
    @property
    @abstractmethod
    def preview_resolution(self) -> Tuple[int, int]:
        """Get the preview resolution (width, height)."""
        pass
