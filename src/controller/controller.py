"""
High-level photo booth controller interface.
Coordinates camera, hardware controller, and session management.
"""

import os
import time
import logging
from typing import Callable, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .serial_controller import SerialController


logger = logging.getLogger(__name__)


@dataclass
class PhotoSession:
    """Represents a photo session with multiple captures."""
    session_id: str
    start_time: datetime
    photos: List[str] = field(default_factory=list)
    completed: bool = False
    
    @property
    def photo_count(self) -> int:
        return len(self.photos)


class PhotoBoothController:
    """
    High-level controller for the photo booth.
    Manages sessions, triggers, and coordinates hardware.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize the photo booth controller.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.controller_config = self.config.get('controller', {})
        self.storage_config = self.config.get('storage', {})
        
        self._serial_controller: Optional[SerialController] = None
        self._current_session: Optional[PhotoSession] = None
        self._capture_callback: Optional[Callable] = None
        self._session_complete_callback: Optional[Callable] = None
        
        self._countdown_seconds = self.controller_config.get('countdown_seconds', 3)
        self._session_dir = self.storage_config.get('session_directory', '/tmp/sessions')
        self._max_photos = self.config.get('ui', {}).get('max_photos_per_session', 10)
    
    def initialize(self) -> bool:
        """Initialize the controller and connect to hardware."""
        if not self.controller_config.get('enabled', True):
            logger.info("Hardware controller disabled in config")
            return True
        
        self._serial_controller = SerialController(self.controller_config)
        
        if self._serial_controller.connect():
            # Register callbacks
            self._serial_controller.register_callback('trigger', self._on_trigger)
            self._serial_controller.register_callback('ready', self._on_ready)
            
            # Set idle state
            self._serial_controller.led_idle()
            
            return True
        
        logger.warning("Controller not connected, running without hardware trigger")
        return False
    
    def shutdown(self) -> None:
        """Shutdown and cleanup."""
        if self._serial_controller is not None:
            self._serial_controller.led_off()
            self._serial_controller.disconnect()
            self._serial_controller = None
    
    def set_capture_callback(self, callback: Callable) -> None:
        """
        Set callback for capture trigger.
        
        Args:
            callback: Function to call when capture should occur
        """
        self._capture_callback = callback
    
    def set_session_complete_callback(self, callback: Callable) -> None:
        """
        Set callback for session completion.
        
        Args:
            callback: Function to call when session is complete
        """
        self._session_complete_callback = callback
    
    def start_session(self) -> PhotoSession:
        """
        Start a new photo session.
        
        Returns:
            The new PhotoSession object
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_path = os.path.join(self._session_dir, session_id)
        os.makedirs(session_path, exist_ok=True)
        
        self._current_session = PhotoSession(
            session_id=session_id,
            start_time=datetime.now()
        )
        
        logger.info(f"Started session: {session_id}")
        
        if self._serial_controller is not None:
            self._serial_controller.led_idle()
        
        return self._current_session
    
    def add_photo_to_session(self, photo_path: str) -> None:
        """
        Add a captured photo to the current session.
        
        Args:
            photo_path: Path to the captured photo
        """
        if self._current_session is not None:
            self._current_session.photos.append(photo_path)
            logger.info(f"Added photo to session: {photo_path}")
    
    def complete_session(self) -> Optional[PhotoSession]:
        """
        Complete the current session.
        
        Returns:
            The completed session, or None if no session active
        """
        if self._current_session is None:
            return None
        
        self._current_session.completed = True
        completed_session = self._current_session
        self._current_session = None
        
        logger.info(f"Session completed: {completed_session.session_id} "
                   f"({completed_session.photo_count} photos)")
        
        if self._session_complete_callback:
            self._session_complete_callback(completed_session)
        
        if self._serial_controller is not None:
            self._serial_controller.led_idle()
        
        return completed_session
    
    def get_current_session(self) -> Optional[PhotoSession]:
        """Get the current session."""
        return self._current_session
    
    def trigger_capture(self) -> None:
        """
        Manually trigger a capture sequence.
        This can be called from UI touch events.
        """
        self._on_trigger()
    
    def start_countdown(self, seconds: Optional[int] = None) -> None:
        """
        Start the LED countdown animation.
        
        Args:
            seconds: Number of seconds (default from config)
        """
        if seconds is None:
            seconds = self._countdown_seconds
        
        if self._serial_controller is not None:
            self._serial_controller.start_countdown(seconds)
    
    def trigger_flash(self) -> None:
        """Trigger the LED flash."""
        if self._serial_controller is not None:
            self._serial_controller.trigger_flash()
    
    def _on_trigger(self) -> None:
        """Handle trigger event from hardware button."""
        logger.info("Capture triggered")
        
        # Check if we have room for more photos
        if self._current_session is None:
            self.start_session()
        
        if self._current_session.photo_count >= self._max_photos:
            logger.warning("Maximum photos reached for session")
            return
        
        # Start countdown
        self.start_countdown()
        
        # Wait for countdown (in real implementation, this would be async)
        time.sleep(self._countdown_seconds)
        
        # Trigger flash
        self.trigger_flash()
        
        # Call capture callback
        if self._capture_callback:
            self._capture_callback()
    
    def _on_ready(self) -> None:
        """Handle ready event from controller."""
        logger.info("Controller ready")
        
        # Set initial LED state
        if self._serial_controller is not None:
            self._serial_controller.led_idle()
    
    def get_session_photos(self, session: Optional[PhotoSession] = None) -> List[str]:
        """
        Get all photos for a session.
        
        Args:
            session: Session to get photos for (default: current)
        
        Returns:
            List of photo file paths
        """
        if session is None:
            session = self._current_session
        
        if session is None:
            return []
        
        return session.photos
    
    def get_session_directory(self, session: Optional[PhotoSession] = None) -> str:
        """
        Get the directory for a session.
        
        Args:
            session: Session (default: current)
        
        Returns:
            Session directory path
        """
        if session is None:
            session = self._current_session
        
        if session is None:
            return self._session_dir
        
        return os.path.join(self._session_dir, session.session_id)
