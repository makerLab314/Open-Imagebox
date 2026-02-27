"""
Live preview widget for camera feed.
"""

import logging
from typing import Optional
import numpy as np

try:
    from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QImage, QPixmap
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    QWidget = object


logger = logging.getLogger(__name__)


class PreviewWidget(QWidget):
    """
    Widget displaying live camera preview.
    Includes capture button overlay.
    """
    
    # Signal emitted when capture is requested
    capture_requested = pyqtSignal() if PYQT5_AVAILABLE else None
    
    def __init__(self, parent=None):
        if not PYQT5_AVAILABLE:
            logger.error("PyQt5 not available")
            return
        
        super().__init__(parent)
        self._setup_ui()
        self._countdown_value = 0
        self._showing_countdown = False
    
    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Preview image label
        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignCenter)
        self._preview_label.setStyleSheet("background-color: black;")
        self._preview_label.setMinimumSize(640, 480)
        layout.addWidget(self._preview_label, 1)
        
        # Countdown overlay label
        self._countdown_label = QLabel()
        self._countdown_label.setAlignment(Qt.AlignCenter)
        self._countdown_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 200px;
                font-weight: bold;
                background-color: transparent;
            }
        """)
        self._countdown_label.setVisible(False)
        
        # Capture button at bottom
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 10, 20, 20)
        
        self._capture_button = QPushButton("📷 FOTO AUFNEHMEN")
        self._capture_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 28px;
                font-weight: bold;
                padding: 20px 40px;
                border-radius: 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #888888;
            }
        """)
        self._capture_button.clicked.connect(self._on_capture_clicked)
        button_layout.addStretch()
        button_layout.addWidget(self._capture_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def update_preview(self, frame: np.ndarray) -> None:
        """
        Update the preview with a new frame.
        
        Args:
            frame: OpenCV BGR image array
        """
        if frame is None:
            return
        
        try:
            # Convert BGR to RGB
            rgb_frame = frame[:, :, ::-1].copy()
            
            height, width, channels = rgb_frame.shape
            bytes_per_line = channels * width
            
            # Create QImage from numpy array
            q_image = QImage(
                rgb_frame.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888
            )
            
            # Scale to fit label while maintaining aspect ratio
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self._preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self._preview_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            logger.error(f"Error updating preview: {e}")
    
    def show_countdown(self, seconds: int) -> None:
        """
        Show countdown overlay.
        
        Args:
            seconds: Number of seconds to count down
        """
        self._countdown_value = seconds
        self._showing_countdown = True
        self._capture_button.setEnabled(False)
        self._update_countdown_display()
        
        # Start countdown timer
        self._countdown_timer = QTimer()
        self._countdown_timer.timeout.connect(self._countdown_tick)
        self._countdown_timer.start(1000)
    
    def _countdown_tick(self) -> None:
        """Handle countdown timer tick."""
        self._countdown_value -= 1
        
        if self._countdown_value <= 0:
            self._countdown_timer.stop()
            self._countdown_label.setVisible(False)
            self._showing_countdown = False
            # Flash effect
            self._flash_effect()
        else:
            self._update_countdown_display()
    
    def _update_countdown_display(self) -> None:
        """Update the countdown display."""
        self._countdown_label.setText(str(self._countdown_value))
        self._countdown_label.setVisible(True)
    
    def _flash_effect(self) -> None:
        """Show flash effect on screen."""
        # Temporarily show white overlay
        self._preview_label.setStyleSheet("background-color: white;")
        QTimer.singleShot(150, self._restore_preview_style)
    
    def _restore_preview_style(self) -> None:
        """Restore preview style after flash."""
        self._preview_label.setStyleSheet("background-color: black;")
        self._capture_button.setEnabled(True)
    
    def _on_capture_clicked(self) -> None:
        """Handle capture button click."""
        if self.capture_requested:
            self.capture_requested.emit()
    
    def set_no_camera_text(self, text: str = "Keine Kamera verbunden") -> None:
        """Show text when no camera is connected."""
        self._preview_label.setText(text)
        self._preview_label.setStyleSheet("""
            background-color: #333;
            color: white;
            font-size: 24px;
        """)
