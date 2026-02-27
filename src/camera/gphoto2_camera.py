"""
GPhoto2 camera implementation for Canon DSLR cameras.
Based on the camera communication approach from self-o-mat.
"""

import os
import time
import tempfile
import logging
from typing import Optional, Tuple, Any

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

try:
    import gphoto2 as gp
    GPHOTO2_AVAILABLE = True
except ImportError:
    GPHOTO2_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from .camera_base import CameraBase


logger = logging.getLogger(__name__)


class GPhoto2Camera(CameraBase):
    """
    Camera implementation using gPhoto2.
    Supports Canon DSLR cameras connected via USB.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize the gPhoto2 camera.
        
        Args:
            config: Configuration dictionary with camera settings.
        """
        self.config = config or {}
        self._camera = None
        self._context = None
        self._connected = False
        self._preview_resolution = (640, 480)
        self._last_preview_time = 0
        self._preview_interval = 1.0 / self.config.get('preview_fps', 15)
        
        if not GPHOTO2_AVAILABLE:
            logger.warning("gPhoto2 Python bindings not available. "
                         "Install with: pip install gphoto2")
    
    def connect(self) -> bool:
        """Connect to the camera via gPhoto2."""
        if not GPHOTO2_AVAILABLE:
            logger.error("gPhoto2 not available")
            return False
        
        try:
            # Initialize gPhoto2 context
            self._context = gp.Context()
            
            # Detect and open camera
            self._camera = gp.Camera()
            self._camera.init(self._context)
            
            # Get camera info
            info = self.get_camera_info()
            logger.info(f"Connected to camera: {info.get('model', 'Unknown')}")
            
            self._connected = True
            return True
            
        except gp.GPhoto2Error as e:
            logger.error(f"Failed to connect to camera: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the camera."""
        if self._camera is not None:
            try:
                self._camera.exit(self._context)
            except Exception as e:
                logger.warning(f"Error during camera disconnect: {e}")
            finally:
                self._camera = None
                self._context = None
                self._connected = False
                logger.info("Camera disconnected")
    
    def is_connected(self) -> bool:
        """Check if camera is connected."""
        return self._connected and self._camera is not None
    
    def get_preview_frame(self) -> Optional[Any]:
        """
        Get a single preview frame from the camera.
        Uses the camera's live view functionality.
        """
        if not self.is_connected():
            return None
        
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            logger.warning("OpenCV or NumPy not available for preview processing")
            return None
        
        # Rate limiting for preview
        current_time = time.time()
        if current_time - self._last_preview_time < self._preview_interval:
            return None
        
        try:
            # Capture preview image
            camera_file = self._camera.capture_preview(self._context)
            
            # Get file data
            file_data = camera_file.get_data_and_size()
            
            # Convert to numpy array using OpenCV
            img_array = np.frombuffer(file_data, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if frame is not None:
                self._preview_resolution = (frame.shape[1], frame.shape[0])
                self._last_preview_time = current_time
                return frame
            
        except gp.GPhoto2Error as e:
            logger.debug(f"Preview capture failed: {e}")
        except Exception as e:
            logger.error(f"Error getting preview frame: {e}")
        
        return None
    
    def capture_image(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Capture a full resolution image.
        
        Args:
            filename: Optional filename to save the image to.
        
        Returns:
            Path to the captured image file, or None on failure.
        """
        if not self.is_connected():
            logger.error("Camera not connected")
            return None
        
        try:
            # Trigger capture
            logger.info("Capturing image...")
            file_path = self._camera.capture(gp.GP_CAPTURE_IMAGE, self._context)
            
            logger.info(f"Camera file: {file_path.folder}/{file_path.name}")
            
            # Download the image
            camera_file = self._camera.file_get(
                file_path.folder,
                file_path.name,
                gp.GP_FILE_TYPE_NORMAL,
                self._context
            )
            
            # Determine output filename
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                ext = os.path.splitext(file_path.name)[1]
                filename = os.path.join(
                    tempfile.gettempdir(),
                    f"capture_{timestamp}{ext}"
                )
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Save to file
            camera_file.save(filename)
            logger.info(f"Image saved to: {filename}")
            
            # Optionally delete from camera
            try:
                self._camera.file_delete(
                    file_path.folder,
                    file_path.name,
                    self._context
                )
            except gp.GPhoto2Error:
                pass  # Some cameras don't support deletion
            
            return filename
            
        except gp.GPhoto2Error as e:
            logger.error(f"Failed to capture image: {e}")
            return None
    
    def get_camera_info(self) -> dict:
        """Get camera information."""
        if not self.is_connected():
            return {}
        
        try:
            abilities = self._camera.get_abilities()
            return {
                'model': abilities.model,
                'status': abilities.status,
                'port': abilities.port,
                'operations': abilities.operations,
            }
        except Exception as e:
            logger.error(f"Failed to get camera info: {e}")
            return {}
    
    def auto_focus(self) -> bool:
        """Trigger auto focus."""
        if not self.is_connected():
            return False
        
        try:
            # Get camera config
            config = self._camera.get_config(self._context)
            
            # Try to find autofocus action
            # Different cameras may have different config paths
            af_paths = [
                '/actions/autofocusdrive',
                '/actions/manualfocusdrive',
                '/capturesettings/autofocus',
            ]
            
            for path in af_paths:
                try:
                    widget = config.get_child_by_name(path.split('/')[-1])
                    widget.set_value(1)
                    self._camera.set_config(config, self._context)
                    logger.info("Auto focus triggered")
                    return True
                except gp.GPhoto2Error:
                    continue
            
            logger.warning("Auto focus not supported or not found")
            return False
            
        except Exception as e:
            logger.error(f"Auto focus failed: {e}")
            return False
    
    @property
    def preview_resolution(self) -> Tuple[int, int]:
        """Get the preview resolution."""
        return self._preview_resolution
    
    def get_config_value(self, name: str) -> Optional[str]:
        """Get a camera configuration value."""
        if not self.is_connected():
            return None
        
        try:
            config = self._camera.get_config(self._context)
            widget = config.get_child_by_name(name)
            return widget.get_value()
        except Exception as e:
            logger.debug(f"Could not get config {name}: {e}")
            return None
    
    def set_config_value(self, name: str, value: str) -> bool:
        """Set a camera configuration value."""
        if not self.is_connected():
            return False
        
        try:
            config = self._camera.get_config(self._context)
            widget = config.get_child_by_name(name)
            widget.set_value(value)
            self._camera.set_config(config, self._context)
            logger.info(f"Set config {name} = {value}")
            return True
        except Exception as e:
            logger.error(f"Could not set config {name}: {e}")
            return False
