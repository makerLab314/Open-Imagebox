"""
Main window for the photo booth application.
Inspired by self-o-mat's GUI state machine:
  INIT → LIVE_PREVIEW → COUNTDOWN → CAPTURE → FINAL_IMAGE → QR_EXPORT → LIVE_PREVIEW
"""

import logging
from typing import Optional

try:
    from PyQt5.QtWidgets import (
        QMainWindow, QWidget, QStackedWidget, QVBoxLayout,
        QApplication, QMessageBox
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSlot
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    QMainWindow = object

from .preview_widget import PreviewWidget
from .gallery_widget import GalleryWidget
from .export_widget import ExportWidget


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for the photo booth.
    Manages different views: preview, gallery, export.
    
    State machine inspired by self-o-mat's BoothLogic:
    - Preview: Live camera feed with capture button
    - Gallery: View captured photos, take more, or finish
    - Export: QR codes for WiFi + download
    """
    
    # View indices
    VIEW_PREVIEW = 0
    VIEW_GALLERY = 1
    VIEW_EXPORT = 2
    
    def __init__(self, config: dict = None):
        if not PYQT5_AVAILABLE:
            logger.error("PyQt5 not available")
            return
        
        super().__init__()
        
        self.config = config or {}
        self.display_config = self.config.get('display', {})
        self.ui_config = self.config.get('ui', {})
        
        self._camera_manager = None
        self._controller = None
        self._web_server = None
        self._sharing_manager = None
        
        self._preview_timer: Optional[QTimer] = None
        self._idle_timer: Optional[QTimer] = None
        self._capturing = False
        
        self._setup_ui()
        self._setup_timers()
    
    def _setup_ui(self):
        """Setup the main window UI."""
        # Window settings
        self.setWindowTitle("Open-Imagebox Photo Booth")
        
        # Dark theme - set before showing
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                background-color: #1a1a1a;
                color: white;
            }
        """)
        
        # Central widget with stacked views
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for different views
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)
        
        # Create views
        self._preview_widget = PreviewWidget()
        self._gallery_widget = GalleryWidget()
        self._export_widget = ExportWidget()
        
        self._stack.addWidget(self._preview_widget)  # Index 0
        self._stack.addWidget(self._gallery_widget)  # Index 1
        self._stack.addWidget(self._export_widget)   # Index 2
        
        # Connect signals
        self._preview_widget.capture_requested.connect(self._on_capture_requested)
        self._gallery_widget.back_to_camera.connect(self._show_preview)
        self._gallery_widget.export_requested.connect(self._show_export)
        self._export_widget.new_session_requested.connect(self._start_new_session)
        
        # Start with preview
        self._stack.setCurrentIndex(self.VIEW_PREVIEW)
    
    def show(self):
        """Show the window with proper fullscreen/windowed mode."""
        if self.display_config.get('fullscreen', True):
            # showFullScreen() internally calls show()
            self.showFullScreen()
            self.setCursor(Qt.BlankCursor)
        else:
            resolution = self.display_config.get('resolution', [1024, 600])
            self.resize(resolution[0], resolution[1])
            super().show()
    
    def _setup_timers(self):
        """Setup application timers."""
        # Preview update timer
        preview_fps = self.config.get('camera', {}).get('preview_fps', 15)
        self._preview_timer = QTimer()
        self._preview_timer.timeout.connect(self._update_preview)
        self._preview_timer.setInterval(int(1000 / preview_fps))
        
        # Idle timeout timer
        idle_timeout = self.ui_config.get('idle_timeout_seconds', 60)
        if idle_timeout > 0:
            self._idle_timer = QTimer()
            self._idle_timer.timeout.connect(self._on_idle_timeout)
            self._idle_timer.setInterval(idle_timeout * 1000)
    
    def set_camera_manager(self, camera_manager) -> None:
        """Set the camera manager instance."""
        self._camera_manager = camera_manager
        if camera_manager and camera_manager.is_connected():
            self._preview_timer.start()
            logger.info("Camera preview started")
        else:
            self._preview_widget.set_no_camera_text(
                "Keine Kamera verbunden\n\n"
                "Bitte Kamera per USB anschließen\n"
                "und Software neu starten.\n\n"
                "No camera connected.\n"
                "Please connect camera via USB\n"
                "and restart the software."
            )
    
    def set_controller(self, controller) -> None:
        """Set the photo booth controller instance."""
        self._controller = controller
        if controller:
            controller.set_capture_callback(self._perform_capture)
    
    def set_web_server(self, web_server) -> None:
        """Set the web server instance."""
        self._web_server = web_server
    
    def set_sharing_manager(self, sharing_manager) -> None:
        """Set the sharing manager instance."""
        self._sharing_manager = sharing_manager
    
    @pyqtSlot()
    def _update_preview(self):
        """Update preview from camera."""
        if self._camera_manager is None:
            return
        
        frame = self._camera_manager.get_preview_frame()
        if frame is not None:
            self._preview_widget.update_preview(frame)
        
        # Reset idle timer on activity
        if self._idle_timer:
            self._idle_timer.start()
    
    @pyqtSlot()
    def _on_capture_requested(self):
        """Handle capture request from UI."""
        if self._capturing:
            return  # Prevent double-capture
        
        if self._controller:
            self._controller.trigger_capture()
        else:
            # Direct capture without controller
            self._start_countdown_and_capture()
    
    def _start_countdown_and_capture(self):
        """Start countdown and capture (without hardware controller)."""
        self._capturing = True
        countdown = self.config.get('controller', {}).get('countdown_seconds', 3)
        self._preview_widget.show_countdown(countdown)
        
        # Schedule capture after countdown
        QTimer.singleShot(countdown * 1000 + 200, self._perform_capture)
    
    def _perform_capture(self):
        """Perform the actual image capture."""
        if self._camera_manager is None or not self._camera_manager.is_connected():
            logger.error("No camera available for capture")
            self._capturing = False
            return
        
        # Ensure we have a session
        if self._controller:
            session = self._controller.get_current_session()
            if session is None:
                session = self._controller.start_session()
            
            # Generate filename
            session_dir = self._controller.get_session_directory()
            filename = f"{session_dir}/photo_{session.photo_count + 1:03d}.jpg"
        else:
            import tempfile
            import time
            filename = f"{tempfile.gettempdir()}/photo_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        
        # Capture image
        result = self._camera_manager.capture_image(filename)
        self._capturing = False
        
        if result:
            logger.info(f"Photo captured: {result}")
            
            # Add to session
            if self._controller:
                self._controller.add_photo_to_session(result)
            
            # Update web server with current session
            if self._web_server and self._controller:
                session = self._controller.get_current_session()
                if session:
                    self._web_server.set_current_session(session.session_id)
            
            # Add to gallery
            self._gallery_widget.add_photo(result)
            
            # Show gallery after capture
            if self.ui_config.get('show_gallery', True):
                self._show_gallery()
        else:
            logger.error("Failed to capture photo")
            self._preview_widget.show_error("Foto konnte nicht aufgenommen werden")
    
    def _show_preview(self):
        """Show preview view."""
        self._stack.setCurrentIndex(self.VIEW_PREVIEW)
        # Ensure preview timer is running
        if self._camera_manager and self._camera_manager.is_connected():
            if not self._preview_timer.isActive():
                self._preview_timer.start()
    
    def _show_gallery(self):
        """Show gallery view."""
        self._stack.setCurrentIndex(self.VIEW_GALLERY)
    
    def _show_export(self):
        """Show export view with QR codes."""
        # Complete the session
        if self._controller:
            self._controller.complete_session()
        
        # Setup sharing info
        sharing_config = self.config.get('sharing', {})
        
        # Set WiFi QR code
        if sharing_config.get('hotspot_enabled', True):
            ssid = sharing_config.get('hotspot_ssid', 'PhotoBooth')
            password = sharing_config.get('hotspot_password', 'photos123')
            self._export_widget.set_wifi_qr(ssid, password)
        
        # Set download URL
        if self._web_server:
            host = self._web_server.get_host_ip()
            port = sharing_config.get('web_port', 8080)
            download_url = f"http://{host}:{port}"
            self._export_widget.set_download_url(download_url)
        
        # Handle OneDrive upload
        if sharing_config.get('onedrive_enabled', False):
            self._export_widget.show_onedrive_uploading()
        
        self._stack.setCurrentIndex(self.VIEW_EXPORT)
    
    def _start_new_session(self):
        """Start a new photo session."""
        # Clear gallery
        self._gallery_widget.clear()
        
        # Start new session
        if self._controller:
            self._controller.start_session()
        
        # Show preview
        self._show_preview()
    
    def _on_idle_timeout(self):
        """Handle idle timeout - return to preview after idle."""
        if self._stack.currentIndex() != self.VIEW_PREVIEW:
            self._start_new_session()
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        # Escape to exit fullscreen
        if event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                self.setCursor(Qt.ArrowCursor)
            else:
                self.close()
        
        # F11 to toggle fullscreen
        elif event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
                self.setCursor(Qt.ArrowCursor)
            else:
                self.showFullScreen()
                self.setCursor(Qt.BlankCursor)
        
        # Space or Enter to capture
        elif event.key() in (Qt.Key_Space, Qt.Key_Return):
            if self._stack.currentIndex() == self.VIEW_PREVIEW:
                self._on_capture_requested()
        
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle window close."""
        # Stop timers
        if self._preview_timer:
            self._preview_timer.stop()
        if self._idle_timer:
            self._idle_timer.stop()
        
        super().closeEvent(event)
