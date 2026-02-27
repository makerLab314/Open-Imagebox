"""
Gallery widget for viewing captured photos.
"""

import os
import logging
from typing import List

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
        QPushButton, QLabel, QGridLayout, QFrame
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QPixmap
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False
    QWidget = object


logger = logging.getLogger(__name__)


class PhotoThumbnail(QFrame if PYQT5_AVAILABLE else object):
    """Clickable photo thumbnail."""
    
    clicked = pyqtSignal(str) if PYQT5_AVAILABLE else None
    
    def __init__(self, photo_path: str, parent=None):
        if not PYQT5_AVAILABLE:
            return
        
        super().__init__(parent)
        self.photo_path = photo_path
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup thumbnail UI."""
        self.setFixedSize(150, 150)
        self.setStyleSheet("""
            QFrame {
                background-color: #444;
                border: 2px solid #666;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #4CAF50;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Thumbnail image
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._load_thumbnail()
        layout.addWidget(self._image_label)
        
        self.setCursor(Qt.PointingHandCursor)
    
    def _load_thumbnail(self):
        """Load and display thumbnail."""
        if os.path.exists(self.photo_path):
            pixmap = QPixmap(self.photo_path)
            scaled = pixmap.scaled(
                130, 130,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self._image_label.setPixmap(scaled)
        else:
            self._image_label.setText("?")
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if self.clicked:
            self.clicked.emit(self.photo_path)
        super().mousePressEvent(event)


class GalleryWidget(QWidget):
    """
    Widget for displaying captured photos in a gallery view.
    """
    
    # Signal when user wants to take more photos
    back_to_camera = pyqtSignal() if PYQT5_AVAILABLE else None
    
    # Signal when user wants to export/finish
    export_requested = pyqtSignal() if PYQT5_AVAILABLE else None
    
    # Signal when a photo is selected for fullscreen view
    photo_selected = pyqtSignal(str) if PYQT5_AVAILABLE else None
    
    def __init__(self, parent=None):
        if not PYQT5_AVAILABLE:
            logger.error("PyQt5 not available")
            return
        
        super().__init__(parent)
        self._photos: List[str] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup gallery UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("📸 Deine Fotos")
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: white;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Photo count
        self._count_label = QLabel("0 Fotos aufgenommen")
        self._count_label.setStyleSheet("font-size: 18px; color: #888;")
        self._count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._count_label)
        
        # Scroll area for thumbnails
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #222;
                border: none;
                border-radius: 10px;
            }
        """)
        
        self._thumbnail_container = QWidget()
        self._thumbnail_layout = QGridLayout(self._thumbnail_container)
        self._thumbnail_layout.setSpacing(15)
        self._thumbnail_layout.setContentsMargins(15, 15, 15, 15)
        
        scroll.setWidget(self._thumbnail_container)
        layout.addWidget(scroll, 1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # Back to camera button
        self._back_button = QPushButton("📷 Mehr Fotos")
        self._back_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 22px;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self._back_button.clicked.connect(self._on_back_clicked)
        button_layout.addWidget(self._back_button)
        
        # Export/Done button
        self._export_button = QPushButton("✅ Fertig / Export")
        self._export_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 22px;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self._export_button.clicked.connect(self._on_export_clicked)
        button_layout.addWidget(self._export_button)
        
        layout.addLayout(button_layout)
    
    def set_photos(self, photos: List[str]) -> None:
        """
        Set the photos to display.
        
        Args:
            photos: List of photo file paths
        """
        self._photos = photos
        self._update_gallery()
    
    def add_photo(self, photo_path: str) -> None:
        """
        Add a photo to the gallery.
        
        Args:
            photo_path: Path to photo file
        """
        self._photos.append(photo_path)
        self._update_gallery()
    
    def clear(self) -> None:
        """Clear all photos from gallery."""
        self._photos = []
        self._update_gallery()
    
    def _update_gallery(self) -> None:
        """Update the gallery display."""
        # Clear existing thumbnails
        while self._thumbnail_layout.count():
            item = self._thumbnail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Update count label
        count = len(self._photos)
        self._count_label.setText(f"{count} Foto{'s' if count != 1 else ''} aufgenommen")
        
        # Add thumbnails
        columns = 4
        for i, photo_path in enumerate(self._photos):
            row = i // columns
            col = i % columns
            
            thumbnail = PhotoThumbnail(photo_path)
            if thumbnail.clicked:
                thumbnail.clicked.connect(self._on_photo_clicked)
            
            self._thumbnail_layout.addWidget(thumbnail, row, col)
        
        # Add stretch to bottom
        self._thumbnail_layout.setRowStretch(
            (len(self._photos) // columns) + 1, 1
        )
    
    def _on_photo_clicked(self, photo_path: str) -> None:
        """Handle photo thumbnail click."""
        if self.photo_selected:
            self.photo_selected.emit(photo_path)
    
    def _on_back_clicked(self) -> None:
        """Handle back button click."""
        if self.back_to_camera:
            self.back_to_camera.emit()
    
    def _on_export_clicked(self) -> None:
        """Handle export button click."""
        if self.export_requested:
            self.export_requested.emit()
